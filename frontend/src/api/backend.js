import axios from "axios";

/** Base URL for the FastAPI backend (e.g. http://localhost:8000) */
const baseURL = import.meta.env.VITE_BACKEND_URL ?? "";

const client = axios.create({ baseURL });

/**
 * @param {string} [room] — omit for a fresh room per session (recommended for agent dispatch)
 * @param {string} [participant]
 * @returns {Promise<{ token: string, ws_url: string, room: string }>}
 */
export async function getToken(room, participant = "user") {
  const params = { participant };
  if (room != null && room !== "") params.room = room;
  const { data } = await client.get("/token", { params });
  return data;
}

/**
 * @param {string} phoneNumber
 * @returns {Promise<object[]>}
 */
export async function getAppointments(phoneNumber) {
  const { data } = await client.get(
    `/appointments/${encodeURIComponent(phoneNumber)}`
  );
  return data;
}
