import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { computed, ref } from "vue";
import GameLayoutControlbar from "@/features/freeplay/GameLayoutControlbar.vue";
import type { GameController } from "@/core/games/types/game-controller";

// Mock i18next
vi.mock("i18next-vue", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock icons
vi.mock("oh-vue-icons", () => ({
  OhVueIcon: { template: "<span />" },
}));

function createMockController(overrides?: Partial<GameController>): GameController {
  return {
    puzzle_type: "sudoku",
    state: computed(() => ({
      solved: false,
      definition: { id: "1", puzzle_type: "sudoku", rows: 9, cols: 9 },
    })),
    ui: ref({
      show_solved_state: false,
      tutorial_mode: false,
      animate_success: false,
      animate_failure: false,
    }),
    current_variant: ref<[string, string]>(["9x9", "easy"]),
    tutorial_used: ref(false),
    formatted_time: computed(() => "00:00"),
    is_daily: computed(() => false),
    daily_date: ref(null),
    check_solution: vi.fn(),
    clear_puzzle: vi.fn(),
    request_new_puzzle: vi.fn(),
    ...overrides,
  };
}

describe("GameLayoutControlbar", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows New Puzzle button in freeplay mode", () => {
    const controller = createMockController();
    const wrapper = mount(GameLayoutControlbar, {
      props: { controller },
      global: {
        stubs: { "v-icon": true },
        mocks: { $t: (key: string) => key },
      },
    });

    expect(wrapper.text()).toContain("freeplay:control.new_puzzle");
  });

  it("hides New Puzzle button in daily mode", () => {
    const controller = createMockController({
      is_daily: computed(() => true),
      daily_date: ref("2026-03-18"),
    });
    const wrapper = mount(GameLayoutControlbar, {
      props: { controller },
      global: {
        stubs: { "v-icon": true },
        mocks: { $t: (key: string) => key },
      },
    });

    expect(wrapper.text()).not.toContain("freeplay:control.new_puzzle");
  });

  it("calls check_solution when submit is clicked", async () => {
    const controller = createMockController();
    const wrapper = mount(GameLayoutControlbar, {
      props: { controller },
      global: {
        stubs: { "v-icon": true },
        mocks: { $t: (key: string) => key },
      },
    });

    const submitBtn = wrapper.findAll("button").find((b) => b.text().includes("ui:action.submit"));
    expect(submitBtn).toBeTruthy();
    await submitBtn!.trigger("click");
    expect(controller.check_solution).toHaveBeenCalled();
  });

  it("calls clear_puzzle when clear is clicked", async () => {
    const controller = createMockController();
    const wrapper = mount(GameLayoutControlbar, {
      props: { controller },
      global: {
        stubs: { "v-icon": true },
        mocks: { $t: (key: string) => key },
      },
    });

    const clearBtn = wrapper.findAll("button").find((b) => b.text().includes("ui:action.clear"));
    expect(clearBtn).toBeTruthy();
    await clearBtn!.trigger("click");
    expect(controller.clear_puzzle).toHaveBeenCalled();
  });
});
