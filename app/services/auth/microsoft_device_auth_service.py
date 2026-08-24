import asyncio
from time import time
from uuid import uuid4

import msal

from app.clients.fabric_client import FabricClient
from app.clients.powerbi_client import PowerBIClient
from app.core.microsoft_auth import (
    FABRIC_SCOPES,
    MICROSOFT_LOGIN_BASE_URL,
    POWERBI_SCOPES,
)
from app.services.auth.device_auth_store import (
    DeviceAuthSession,
    get_device_session,
    save_device_session,
)

class MicrosoftDeviceAuthService:

    async def _wait_for_authentication(
        self,
        *,
        session_id: str,
    ) -> None:
        session = get_device_session(
            session_id
        )

        if session is None:
            return

        authority = (
            f"{MICROSOFT_LOGIN_BASE_URL}/"
            f"{session.tenant_id}"
        )

        app = msal.PublicClientApplication(
            client_id=session.client_id,
            authority=authority,
        )

        try:
            result = await asyncio.to_thread(
                app.acquire_token_by_device_flow,
                session.flow,
            )

            access_token = result.get(
                "access_token"
            )

            if not access_token:
                session.status = "failed"

                session.error_message = (
                    result.get(
                        "error",
                        "authentication_failed",
                    )
                )

                return

            expires_in = int(
                result.get(
                    "expires_in",
                    3600,
                )
            )

            powerbi_expires_at = (
                time()
                + max(
                    expires_in - 60,
                    60,
                )
            )

            powerbi_client = PowerBIClient()

            await powerbi_client.validate_connection(
                access_token
            )

            session.powerbi_access_token = (
                access_token
            )

            session.powerbi_token_expires_at = (
                powerbi_expires_at
            )

            session.powerbi_connected = True

            #
            # Attempt Fabric authentication
            # silently using MSAL's cached account.
            #
            await self._try_acquire_fabric_token(
                app=app,
                session=session,
            )

            session.status = "authenticated"

            session.flow.clear()

        except Exception:
            session.status = "failed"

            session.powerbi_access_token = None

            session.error_message = (
                "Microsoft authentication "
                "or Power BI validation failed."
            )

    async def _wait_for_fabric_authentication(
        self,
        *,
        session_id: str,
    ) -> None:
        session = get_device_session(
            session_id
        )

        if session is None:
            return

        authority = (
            f"{MICROSOFT_LOGIN_BASE_URL}/"
            f"{session.tenant_id}"
        )

        app = msal.PublicClientApplication(
            client_id=session.client_id,
            authority=authority,
        )

        try:
            result = await asyncio.to_thread(
                app.acquire_token_by_device_flow,
                session.fabric_flow,
            )

            access_token = result.get(
                "access_token"
            )

            if not access_token:
                session.fabric_connected = False

                session.fabric_error_code = (
                    result.get(
                        "error",
                        "fabric_authentication_failed",
                    )
                )

                return

            expires_in = int(
                result.get(
                    "expires_in",
                    3600,
                )
            )

            expires_at = (
                time()
                + max(
                    expires_in - 60,
                    60,
                )
            )

            fabric_client = FabricClient()

            await fabric_client.validate_connection(
                access_token
            )

            session.fabric_access_token = (
                access_token
            )

            session.fabric_token_expires_at = (
                expires_at
            )

            session.fabric_connected = True
            session.fabric_error_code = None

            session.fabric_flow.clear()

        except Exception:
            session.fabric_access_token = None
            session.fabric_connected = False

            session.fabric_error_code = (
                "fabric_authentication_failed"
            )

    async def _try_acquire_fabric_token(
        self,
        *,
        app: msal.PublicClientApplication,
        session: DeviceAuthSession,
    ) -> None:
        accounts = app.get_accounts()

        if not accounts:
            session.fabric_connected = False
            session.fabric_error_code = (
                "account_not_cached"
            )

            return

        account = accounts[0]

        try:
            result = await asyncio.to_thread(
                app.acquire_token_silent_with_error,
                FABRIC_SCOPES,
                account=account,
            )

            if not result:
                session.fabric_connected = False
                session.fabric_error_code = (
                    "interaction_required"
                )

                return

            access_token = result.get(
                "access_token"
            )

            if not access_token:
                session.fabric_connected = False

                session.fabric_error_code = (
                    result.get(
                        "error",
                        "interaction_required",
                    )
                )

                return

            expires_in = int(
                result.get(
                    "expires_in",
                    3600,
                )
            )

            expires_at = (
                time()
                + max(
                    expires_in - 60,
                    60,
                )
            )

            fabric_client = FabricClient()

            await fabric_client.validate_connection(
                access_token
            )

            session.fabric_access_token = (
                access_token
            )

            session.fabric_token_expires_at = (
                expires_at
            )

            session.fabric_connected = True
            session.fabric_error_code = None

        except Exception:
            session.fabric_access_token = None
            session.fabric_connected = False

            session.fabric_error_code = (
                "fabric_validation_failed"
            )

    async def start(
        self,
        *,
        tenant_id: str,
        client_id: str,
    ) -> tuple[str, dict]:
        authority = (
            f"{MICROSOFT_LOGIN_BASE_URL}/"
            f"{tenant_id}"
        )

        app = msal.PublicClientApplication(
            client_id=client_id,
            authority=authority,
        )

        flow = app.initiate_device_flow(
            scopes=POWERBI_SCOPES,
        )

        if "user_code" not in flow:
            raise RuntimeError(
                "Microsoft device authentication "
                "could not be started."
            )

        session_id = str(
            uuid4()
        )

        save_device_session(
            session_id,
            DeviceAuthSession(
                tenant_id=tenant_id,
                client_id=client_id,
                flow=flow,
            ),
        )

        asyncio.create_task(
            self._wait_for_authentication(
                session_id=session_id,
            )
        )

        return session_id, flow

    async def start_fabric_authentication(
        self,
        *,
        session_id: str,
    ) -> dict:
        session = get_device_session(
            session_id
        )

        if session is None:
            raise RuntimeError(
                "Authentication session "
                "does not exist."
            )

        authority = (
            f"{MICROSOFT_LOGIN_BASE_URL}/"
            f"{session.tenant_id}"
        )

        app = msal.PublicClientApplication(
            client_id=session.client_id,
            authority=authority,
        )

        flow = app.initiate_device_flow(
            scopes=FABRIC_SCOPES,
        )

        if "user_code" not in flow:
            raise RuntimeError(
                "Fabric authentication "
                "could not be started."
            )

        session.fabric_flow = flow

        asyncio.create_task(
            self._wait_for_fabric_authentication(
                session_id=session_id,
            )
        )

        return flow