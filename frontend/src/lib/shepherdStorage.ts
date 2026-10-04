const DECLINED_KEY = "papyrus.shepherd.declined";
const COMPLETED_KEY = "papyrus.shepherd.completed";

export function shepherdDeclined(): boolean {
  try {
    return localStorage.getItem(DECLINED_KEY) === "1";
  } catch {
    return false;
  }
}

export function shepherdCompleted(): boolean {
  try {
    return localStorage.getItem(COMPLETED_KEY) === "1";
  } catch {
    return false;
  }
}

export function markShepherdDeclined(): void {
  try {
    localStorage.setItem(DECLINED_KEY, "1");
  } catch {
    /* private mode */
  }
}

export function markShepherdCompleted(): void {
  try {
    localStorage.setItem(COMPLETED_KEY, "1");
  } catch {
    /* private mode */
  }
}

export function shouldOfferShepherdMode(): boolean {
  return !shepherdDeclined() && !shepherdCompleted();
}
