import { inject } from "vue"
import { NetDriver } from "@/services/transport/netdriver.ts"
import { type IGameService, WebsocketGameService } from "./WebsocketGameService.ts";

export function provideGameService() {
  const gs = new WebsocketGameService(new NetDriver({
    url: () => `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/puzzlet/`,
    heartbeatMs: 2000,
    autoReconnect: true
  }))
  gs.connect()
  return gs
}

export function useGameService(): IGameService {
  const gs = inject<IGameService>("GameService")
  if (!gs) throw new Error("GameService not provided")
  return gs
}
