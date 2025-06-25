// src/store/game.ts ----------------------------------------------------------
import { defineStore } from "pinia"
import { reactive, readonly } from "vue"
import type {
  EventState,        // generated from protocol
  EventSolved,
  EventError,
  PayloadPuzzleType, // "sudoku" | "lightup" | …
} from "@/codegen/websocket/game.schema"

type GameAction = number;

/** Flat board + meta info for a single session */
export interface SessionSnapshot {
  sessionId: string
  puzzle:    PayloadPuzzleType
  board:     number[]
  rows:      number
  cols:      number
  solved:    boolean
  meta:      Record<string, any>       // e.g. clues, mines, givens
  rtt?:      number                    // convenience for UI
}

/** Map <sessionId → snapshot>; keep this *reactive* */
type SessionMap = Record<string, SessionSnapshot>

export const useGameStateStore = defineStore("game", () => {
  // ---------------------------------------------------------------- session data
  const _sessions = reactive<SessionMap>({})

  /** get immutable copy for a component (won’t accidentally mutate) */
  function get(sid: string) {
    return readonly(_sessions[sid]) as SessionSnapshot | undefined
  }

  /** write authoritative events coming from an adapter */
  function apply(event: EventState | EventSolved | EventError) {
    switch (event.kind) {
      case "state":   _applyState(event);  break
      case "solved":  _applySolved(event); break
      case "error":   /* you pick: toast, log, etc. */ break
    }
  }

  // ---------------------------------------------------------------- input queue
  const _pending: GameAction[] = []
  function enqueue(action: GameAction) { _pending.push(action) }
  function dequeueAll(): GameAction[]   { return _pending.splice(0) }

  // ------------------------------------------------------------------ internals
  function _applyState(ev: EventState) {
    _sessions[ev.session_id] = {
      sessionId: ev.session_id,
      puzzle:    ev.puzzle,
      rows:      ev.rows,
      cols:      ev.cols,
      board:     [...ev.board],
      solved:    false,
      meta:      ev.meta ?? {},
    }
  }

  function _applySolved(ev: EventSolved) {
    if (_sessions[ev.session_id]) _sessions[ev.session_id].solved = true
  }

  return {
    // public API
    get,
    apply,
    enqueue,
    dequeueAll,
    // maybe expose the full map if an admin screen needs it
    _sessions,
  }
})
