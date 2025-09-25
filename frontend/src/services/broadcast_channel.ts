/**
 * broadcast channel service - synchronizes game state across multiple tabs
 * uses browser's broadcast channel api to keep puzzle progress in sync
 */

interface GameStateMessage {
  type: 'game_state_update' | 'game_reset' | 'game_solved' | 'tutorial_used' | 'new_puzzle';
  puzzle_type: string;
  data: any;
  timestamp: number;
  source_action?: boolean; // true if this tab initiated the action
}

class BroadcastChannelService {
  private channel: BroadcastChannel;
  private listeners: Map<string, Set<(message: GameStateMessage) => void>> = new Map();

  constructor() {
    this.channel = new BroadcastChannel('puzzle_game_sync');
    this.channel.addEventListener('message', this.handle_message.bind(this));
  }

  private handle_message(event: MessageEvent<GameStateMessage>) {
    const message = event.data;
    const type_listeners = this.listeners.get(message.type);
    
    if (type_listeners) {
      type_listeners.forEach(callback => callback(message));
    }
  }

  /**
   * broadcast game state update to other tabs
   */
  broadcast_state_update(puzzle_type: string, board_state: number[][]) {
    board_state = JSON.parse(JSON.stringify(board_state)); // deep copy to avoid copy issues
    this.channel.postMessage({
      type: 'game_state_update',
      puzzle_type,
      data: { board_state },
      timestamp: Date.now()
    } satisfies GameStateMessage);
  }

  /**
   * broadcast game reset to other tabs
   */
  broadcast_game_reset(puzzle_type: string, initial_state: number[][]) {
    initial_state = JSON.parse(JSON.stringify(initial_state)); // deep copy to avoid copy issues
    this.channel.postMessage({
      type: 'game_reset',
      puzzle_type,
      data: { initial_state },
      timestamp: Date.now()
    } satisfies GameStateMessage);
  }

  /**
   * broadcast puzzle solved status to other tabs
   */
  broadcast_game_solved(puzzle_type: string, timestamp_finish: number) {
    this.channel.postMessage({
      type: 'game_solved',
      puzzle_type,
      data: { timestamp_finish },
      timestamp: Date.now()
    } satisfies GameStateMessage);
  }

  /**
   * broadcast tutorial usage to other tabs
   */
  broadcast_tutorial_used(puzzle_type: string) {
    this.channel.postMessage({
      type: 'tutorial_used',
      puzzle_type,
      data: {},
      timestamp: Date.now()
    } satisfies GameStateMessage);
  }

  /**
   * broadcast new puzzle loaded to other tabs
   */
  broadcast_new_puzzle(puzzle_type: string, puzzle_definition: any) {
    puzzle_definition = JSON.parse(JSON.stringify(puzzle_definition)); // deep copy
    this.channel.postMessage({
      type: 'new_puzzle',
      puzzle_type,
      data: { puzzle_definition },
      timestamp: Date.now()
    } satisfies GameStateMessage);
  }

  /**
   * listen for specific message types
   */
  subscribe(message_type: GameStateMessage['type'], callback: (message: GameStateMessage) => void) {
    if (!this.listeners.has(message_type)) {
      this.listeners.set(message_type, new Set());
    }
    this.listeners.get(message_type)!.add(callback);

    // return unsubscribe function
    return () => {
      const type_listeners = this.listeners.get(message_type);
      if (type_listeners) {
        type_listeners.delete(callback);
        if (type_listeners.size === 0) {
          this.listeners.delete(message_type);
        }
      }
    };
  }

  /**
   * cleanup - close broadcast channel
   */
  destroy() {
    this.channel.close();
    this.listeners.clear();
  }
}

// singleton instance
export const broadcast_channel_service = new BroadcastChannelService();
