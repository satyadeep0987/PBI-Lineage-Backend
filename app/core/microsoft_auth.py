MICROSOFT_LOGIN_BASE_URL = (
    "https://login.microsoftonline.com"
)


POWERBI_RESOURCE = (
    "https://analysis.windows.net/powerbi/api"
)

FABRIC_RESOURCE = (
    "https://api.fabric.microsoft.com/"
)

POWERBI_SCOPES = [
    f"{POWERBI_RESOURCE}/Workspace.Read.All",
    f"{POWERBI_RESOURCE}/Report.Read.All",
    f"{POWERBI_RESOURCE}/Dataset.Read.All",
]


FABRIC_SCOPES = [
    f"{FABRIC_RESOURCE}/Workspace.Read.All",
    f"{FABRIC_RESOURCE}/Item.Read.All",
]


MICROSOFT_TEST_SCOPES = [
    (
        "https://analysis.windows.net/"
        "powerbi/api/Workspace.Read.All"
    ),
]