import { api } from "@/services/axios";

////////////////////////////////////////////////////////////////////////////////
// Types
export type PayloadResponse = {
  status: number;
  data: any;
  meta: any;
  errors: any;
};

export type AuthInfo = {
  username?: string;
  email?: string;
  password: string;
};

////////////////////////////////////////////////////////////////////////////////
// Constants
// API Specification: https://docs.allauth.org/en/latest/headless/openapi-specification/
export const BASE_URL = "/_allauth/browser/v1";
export const ENDPOINTS = Object.freeze({
  ///////////////////////////////
  // Meta
  config: "/config",

  ///////////////////////////////
  // Basics
  signup: "/auth/signup",
  login: "/auth/login",
  session: "/auth/session",
});

async function request(method: string, url: string, data?: any) {
  let options = {
    method: method,
    url: `${BASE_URL}${url}`,
    data: undefined,
  };
  if (data !== undefined) options.data = data;
  return api
    .request(options)
    .then((response) => response.data)
    .catch((error) => error.response.data);
}

export async function signup(payload: AuthInfo): Promise<PayloadResponse> {
  return await request("post", ENDPOINTS.signup, payload);
}
export async function login(payload: AuthInfo): Promise<PayloadResponse> {
  return await request("post", ENDPOINTS.login, payload);
}
export async function logout(): Promise<PayloadResponse> {
  return await request("delete", ENDPOINTS.session);
}
export async function getSession(): Promise<PayloadResponse> {
  return await request("get", ENDPOINTS.session);
}

////////////////////////////////////////////////////////////////////////////////
// Utility Functions

/**
 * 
 * @param errors The error list of objects to aggregate over
s * @returns 
 */
export function aggregateErrorMessages(errors: Array<Object>) {
  return errors.reduce(
    (res: Record<string, Array<string>>, current: any) => {
      const key = current.param;
      if (!res[key]) res[key] = [];
      res[key].push(current.message);
      return res;
    },
    {} as Record<string, Array<string>>,
  );
}
