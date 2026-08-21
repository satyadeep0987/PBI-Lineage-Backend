MICROSOFT_LOGIN_BASE_URL = (
    "https://login.microsoftonline.com"
)


POWERBI_RESOURCE = (
    "https://analysis.windows.net/powerbi/api"
)


POWERBI_SCOPES = [
    f"{POWERBI_RESOURCE}/Workspace.Read.All",
    f"{POWERBI_RESOURCE}/Report.Read.All",
    f"{POWERBI_RESOURCE}/Dataset.Read.All",
]


FABRIC_SCOPES = [
    f"{POWERBI_RESOURCE}/Workspace.Read.All",
    f"{POWERBI_RESOURCE}/Item.Read.All",
]