import { createApp } from 'vue'
import { createPinia } from "pinia"
import { createRouter, createWebHistory, type RouterOptions } from 'vue-router'
import App from './App.vue'
import './style.css'

/**
 * Function to help with generating path dictinary that will be used in routerConfig
 * @param path the path for this view
 * @param name the path name (for referencing in other functions)
 * @param comp the component to be displayed at this endpoint
 * @returns a routerConfig
 */
const path = (path: string, name: string, comp: string) => {
    return {
        path: path,
        name: name,
        component: () => import(`./components/views/${comp}.vue`)
    }
}

const game = (name: string) => {
    return {
        path: `/${name}`,
        name: `game-${name}`,
        component: () => import(`./components/games/${name}/${name}.freeplay.vue`)
    }
}

const routerConfig: RouterOptions = {
    history: createWebHistory(),
    routes: [
        path('', 'Home', 'Home'),
        path('/about-us', 'about-us', 'AboutUs'),
        game('minesweeper'),
        game('sudoku'),
        game('tents'),
        game('kakurasu'),
        { path: '/:pathMatch(.*)*', name: '404', component: () => import('./components/views/404.vue') }
    ]
};

////////////////////////////////////////////////////////////////////////////////
// Add OhVueIcons (https://oh-vue-icons.js.org/)
import { OhVueIcon, addIcons } from "oh-vue-icons";
import { FaUndoAlt, FaRedoAlt } from "oh-vue-icons/icons";
addIcons(FaUndoAlt, FaRedoAlt);

createApp(App)
    .use(createPinia())
    .use(createRouter(routerConfig))
    .component("v-icon", OhVueIcon)
    .mount('#app')
