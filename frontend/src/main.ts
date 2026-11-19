import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import { session } from './state/session'
import './style.css'
const router = createRouter({ history: createWebHashHistory(), routes: ['/', '/communication', '/stories', '/practice', '/login', '/companions', '/account'].map(path => ({ path, component: { template: '<span />' } })), scrollBehavior: () => ({ top: 0 }) })
router.beforeEach(to => {
  if (!session.user) return to.path === '/login' ? true : '/login'
  if (session.user.role === 'child' && !session.companionReady) return to.path === '/companions' ? true : '/companions'
  if (to.path === '/login') return '/'
  if (session.user.role === 'parent' && ['/companions', '/stories', '/practice'].includes(to.path)) return '/'
  return true
})
createApp(App).use(router).mount('#app')
