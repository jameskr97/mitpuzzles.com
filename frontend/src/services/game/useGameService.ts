import { inject } from "vue"
import { NetDriver } from "@/services/transport/netdriver.ts"
import { type IGameServiceEvents, WebsocketGameService } from "./WebsocketGameService.ts";

export function provideGameService() {
  const gs = new WebsocketGameService(new NetDriver({
    url: () => `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/puzzlet/`,
    heartbeatMs: 2000,
    autoReconnect: false
  }))
  gs.connect()
  return gs
}

export function useGameService(): IGameServiceEvents {
  const gs = inject<IGameServiceEvents>("GameService")
  if (!gs) throw new Error("GameService not provided")
  return gs
}
