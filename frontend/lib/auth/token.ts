const ACCESS_TOKEN_KEY = "beyondresume_access_token";

function canUseSessionStorage(): boolean {
  return typeof window !== "undefined" && typeof sessionStorage !== "undefined";
}

export function getAccessToken(): string | null {
  if (!canUseSessionStorage()) {
    return null;
  }

  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (!canUseSessionStorage()) {
    return;
  }

  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (!canUseSessionStorage()) {
    return;
  }

  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}
