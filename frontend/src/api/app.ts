import { api } from "@/lib/axios";

////////////////////////////////////////////////////////////////////////////////
// Endpoints
async function request(method: string, url: string, data?: any) {
    let options = {
        url,
        method: method,
        data: undefined,
    }
    if (data !== undefined) options.data = data;
    return api.request(options)
        .then((response) => response.data)
        .catch((error) => error.response.data);
}

export async function getAppSettings(): Promise<any> {
    return await request('get', '/api/config/game-settings');
}

export async function getRandomPuzzle(): Promise<any> {
    return await request('get', '/api/puzzle/random');
}
