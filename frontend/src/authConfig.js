import { PublicClientApplication } from "@azure/msal-browser";

export const msalConfig = {
    auth: {
        clientId: "b2d79546-175d-4a3e-9e0a-466bd6d291b6",
        authority: "https://compliancechat.ciamlogin.com/46f1d642-3c77-472b-8482-58028085c788/v2.0",
        knownAuthorities: ["compliancechat.ciamlogin.com"],
        redirectUri: "http://localhost:5173",
        postLogoutRedirectUri: "http://localhost:5173"
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

export const loginRequest = {
    scopes: ["openid", "offline_access"]
};

export const msalInstance = new PublicClientApplication(msalConfig);
