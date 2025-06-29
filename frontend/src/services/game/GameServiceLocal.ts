// services/GameServiceLocal.ts
import mitt from "mitt";
import { ref } from "vue";
import type { IGameService } from "@/services/game/WebsocketGameService.ts";

export class GameServiceLocal implements IGameService<{}> {
  readonly bus = mitt<{}>(); // same event bus as remote version
  public state = ref<any>(null); // reactive puzzle state
  readonly connected = ref(true); // always connected in local mode

  constructor(initialState: any) {
    this.state.value = structuredClone(initialState);
  }

  async connect(){}
  send(_kind: string, _payload: any){}
  action(cmd: any){}
  clear(game_id: string): void {}
  load(puzzle_type: string): void {}
  refresh(game_id: string, size: string | undefined, difficulty: string | undefined): void {}
  resume(attempt_id: string): void {}
  setTutorialEnabled(session_id: string, puzzle_type: string, enabled: boolean): void {}
  submit(game_id: string, puzzle_type: string, duration: number): void {}
}
