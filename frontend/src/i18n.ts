import i18next from "i18next";
import I18NextVue from 'i18next-vue';

// english
import en_common from "./locales/en/common.json";
import en_auth from "./locales/en/auth.json";
import en_ui from "./locales/en/ui.json";
import en_freeplay from "./locales/en/freeplay.json";
import en_home from "./locales/en/home.json";
import en_account from "./locales/en/account.json";
// puzzles - english
import en_puzzle_kakurasu from "./locales/en/puzzle/kakurasu.json"
import en_puzzle_sudoku from "./locales/en/puzzle/sudoku.json"
import en_puzzle_lightup from "./locales/en/puzzle/lightup.json"
import en_puzzle_minesweeper from "./locales/en/puzzle/minesweeper.json"
import en_puzzle_mosaic from "./locales/en/puzzle/mosaic.json"
import en_puzzle_nonograms from "./locales/en/puzzle/nonograms.json"
import en_puzzle_tents from "./locales/en/puzzle/tents.json"
import en_puzzle_hashi from "./locales/en/puzzle/hashi.json"
import en_puzzle_norinori from "./locales/en/puzzle/norinori.json"
import en_puzzle_aquarium from "./locales/en/puzzle/aquarium.json"
import en_puzzle_yinyang from "./locales/en/puzzle/yinyang.json"
import en_daily from "./locales/en/daily.json"


i18next.init({
  lng: "en",
  fallbackLng: "en",
  ns: ["common", "auth", "home", "dashboard", "daily"],
  defaultNS: "common",
  resources: {
    en: {
      common: en_common,
      auth: en_auth,
      ui: en_ui,
      freeplay: en_freeplay,
      home: en_home,
      account: en_account,
      daily: en_daily,
      puzzle: {
        kakurasu: en_puzzle_kakurasu,
        sudoku: en_puzzle_sudoku,
        lightup: en_puzzle_lightup,
        minesweeper: en_puzzle_minesweeper,
        mosaic: en_puzzle_mosaic,
        nonograms: en_puzzle_nonograms,
        tents: en_puzzle_tents,
        hashi: en_puzzle_hashi,
        norinori: en_puzzle_norinori,
        aquarium: en_puzzle_aquarium,
        yinyang: en_puzzle_yinyang,
      },
    },
  },
});


export { i18next, I18NextVue }
