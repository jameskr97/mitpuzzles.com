# Store Architecture Documentation

This directory contains the application's state management stores, organized by storage layer and responsibility.

## Storage Layers

### 1. localStorage (Simple Preferences)
- **`usePuzzleScaleStore.ts`** - UI zoom/scale preferences per puzzle type
  - scale value per-puzzle
  - remapped scales for ui 
- **`useCacheVersionStore.ts`** - Cache invalidation version management
    - version-based invalidation
    - auto-clear HTTPCache/localstore on version bump

### 2. HTTPCache (API Responses)
- **`useGameMetadataStore.ts`** - Store Puzzle catalog information (what size/difficulty are available, current selection)
  - current puzzle type/size/difficulty
  - available variants fetched from API (cached in HTTPCache)
- **`usePuzzleDefinitionStore.ts`** - Puzzle definitions fetched from API (stored in HTTPCache, localstore for current puzzle IDs)
  - request new puzzles from server
  - cache puzzle definitions with TTL
  - track "current puzzle" per puzzle type
- **`useFreeplayLeaderboardStore.ts`** - Leaderboard data with HTTP caching
  - Fetch leaderboards per puzzle variant
  - cache with refresh capability

### 3. IndexedDB (Complex Data)
- **`usePuzzleProgressStore.ts`** - Combined puzzle state + timing data
  - timer management (start/pause/stop)
  - puzzle completion tracking (duration, solve status)
  - current puzzle state persistence (2D game boards)

- **`useGameHistoryStore.ts`** - Event tracking for freeplay and experiments
  - Developer API: Simple event tracking for freeplay
  - Researcher API: Complex experiment event tracking
  - Upload completed attempts to server

