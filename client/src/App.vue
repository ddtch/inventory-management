<template>
  <div class="app">
    <!-- ─── Sidebar ─── -->
    <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
      <div class="sidebar-brand">
        <p class="brand-name">{{ t('nav.companyName') }}</p>
        <p class="brand-sub">{{ t('nav.subtitle') }}</p>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <rect x="2" y="2" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="10" y="2" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="2" y="10" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="10" y="10" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M9 2L16 5.5V12.5L9 16L2 12.5V5.5L9 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M9 9V16" stroke="currentColor" stroke-width="1.5"/>
            <path d="M2 5.5L9 9L16 5.5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" :class="{ active: $route.path === '/orders' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <rect x="3" y="3" width="12" height="13" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 1.5V4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M12 1.5V4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M6 8H12M6 11H10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/spending" :class="{ active: $route.path === '/spending' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M9 4.5V5M9 13V13.5M6.5 7.25C6.5 6.422 7.172 5.75 8 5.75H9.5C10.328 5.75 11 6.422 11 7.25C11 8.078 10.328 8.75 9.5 8.75H8.5C7.672 8.75 7 9.422 7 10.25C7 11.078 7.672 11.75 8.5 11.75H10C10.828 11.75 11.5 11.078 11.5 10.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" :class="{ active: $route.path === '/demand' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M2 13.5L6.5 8.5L10 11.5L16 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 5H16V9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M3 9C3 6.239 5.239 4 8 4H14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M15 9C15 11.761 12.761 14 10 14H3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M11.5 2L14.5 4L11.5 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M6.5 12L3.5 14L6.5 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link to="/reports" :class="{ active: $route.path === '/reports' }" @click="sidebarOpen = false">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M2 16H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <rect x="3" y="9" width="3" height="7" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
            <rect x="7.5" y="5" width="3" height="11" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
            <rect x="12" y="2" width="3" height="14" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span>{{ t('nav.reports') }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- Mobile scrim -->
    <div
      v-if="sidebarOpen"
      class="sidebar-scrim"
      @click="sidebarOpen = false"
    ></div>

    <!-- ─── Workspace ─── -->
    <div class="workspace">
      <div class="workspace-topbar">
        <button class="menu-btn" @click="sidebarOpen = true" aria-label="Open navigation">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- ─── Modals (unchanged) ─── -->
    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const sidebarOpen = ref(false)

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      sidebarOpen,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ─── Design tokens ─── */
:root {
  --canvas:      #efe8dc;
  --ink:         #1c1914;
  --muted:       #6f6558;
  --surface:     #f7f3ec;
  --hairline:    #e2d8c8;
  --sidebar-bg:  #1e2420;
  --copper:      #d06a2b;
  --sidebar-w:   252px;
}

/* ─── Reset ─── */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Atkinson Hyperlegible', sans-serif;
  background: var(--canvas);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

*:focus-visible {
  outline: 2px solid var(--copper);
  outline-offset: 2px;
}

/* ─── App shell ─── */
.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

/* ─── Sidebar ─── */
.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  flex-shrink: 0;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 200;
  /* No overflow on the sidebar itself so footer dropdowns can escape */
}

.sidebar-brand {
  padding: 1.375rem 1.25rem 1.125rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  flex-shrink: 0;
}

.brand-name {
  font-family: 'Fraunces', serif;
  font-size: 1.0625rem;
  font-weight: 600;
  color: #f6efe4;
  letter-spacing: -0.01em;
  line-height: 1.25;
  margin-bottom: 0.25rem;
}

.brand-sub {
  font-size: 0.6875rem;
  color: #706860;
  font-weight: 400;
  letter-spacing: 0.01em;
  line-height: 1.4;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;        /* critical: allows flex child to shrink + scroll */
  padding: 0.625rem 0;
  overflow-y: auto;
  overflow-x: visible;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6875rem 1.25rem;
  text-decoration: none;
  color: #c9c1b4;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  border-left: 3px solid transparent;
  white-space: nowrap;
}

.sidebar-nav a:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e8dfd4;
}

.sidebar-nav a.active {
  background: rgba(208, 106, 43, 0.16);
  color: #f6efe4;
  border-left-color: var(--copper);
}

.sidebar-nav a svg {
  flex-shrink: 0;
  opacity: 0.75;
}

.sidebar-nav a:hover svg {
  opacity: 0.9;
}

.sidebar-nav a.active svg {
  opacity: 1;
  color: var(--copper);
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 0.875rem 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  overflow: visible; /* let dropdowns escape upward */
  position: relative;
}

/* ─── Scrim (mobile only) ─── */
.sidebar-scrim {
  position: fixed;
  inset: 0;
  background: rgba(28, 25, 20, 0.52);
  z-index: 190;
}

/* ─── Workspace ─── */
.workspace {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.workspace-topbar {
  display: none;
  align-items: center;
  padding: 0.625rem 1.25rem;
  border-bottom: 1px solid var(--hairline);
  background: var(--surface);
  position: sticky;
  top: 0;
  z-index: 100;
}

.menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background: transparent;
  border: 1px solid var(--hairline);
  border-radius: 8px;
  cursor: pointer;
  color: var(--ink);
  transition: background 0.15s;
}

.menu-btn:hover {
  background: var(--canvas);
}

.main-content {
  flex: 1;
  padding: 1.5rem 1.75rem 2.5rem;
}

/* ─── Page header ─── */
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.875rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 0.375rem;
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--muted);
  font-size: 0.9375rem;
}

/* ─── Stats grid ─── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--surface);
  padding: 1.25rem;
  border-radius: 14px;
  border: 1px solid var(--hairline);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: #cdc3b2;
  box-shadow: 0 4px 16px rgba(28, 25, 20, 0.07);
}

.stat-label {
  color: var(--muted);
  font-size: 0.8125rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-family: 'Fraunces', serif;
  font-size: 2.25rem;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.02em;
}

.stat-card.warning .stat-value { color: #b5521a; }
.stat-card.success .stat-value { color: #276640; }
.stat-card.danger  .stat-value { color: #a52020; }
.stat-card.info    .stat-value { color: #1b4e8a; }

/* ─── Card ─── */
.card {
  background: var(--surface);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid var(--hairline);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--hairline);
}

.card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.015em;
}

/* ─── Tables ─── */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--canvas);
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 700;
  color: var(--muted);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--hairline);
  color: var(--ink);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--canvas);
}

/* ─── Badges ─── */
.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge.success    { background: #cee8d8; color: #1a5934; }
.badge.warning    { background: #f2dfc0; color: #733b0e; }
.badge.danger     { background: #f2d0d0; color: #851c1c; }
.badge.info       { background: #cfdded; color: #183d6b; }
.badge.increasing { background: #cee8d8; color: #1a5934; }
.badge.decreasing { background: #f2d0d0; color: #851c1c; }
.badge.stable     { background: #dbd6ef; color: #3a3183; }
.badge.high       { background: #f2d0d0; color: #851c1c; }
.badge.medium     { background: #f2dfc0; color: #733b0e; }
.badge.low        { background: #cfdded; color: #183d6b; }

/* ─── States ─── */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--muted);
  font-size: 0.9375rem;
}

.error {
  background: #f9eaea;
  border: 1px solid #e0b0b0;
  color: #851c1c;
  padding: 1rem;
  border-radius: 12px;
  margin: 1rem 0;
  font-size: 0.9375rem;
}

/* ─── Responsive: mobile sidebar ─── */
@media (max-width: 899px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }

  .sidebar.sidebar--open {
    transform: translateX(0);
  }

  .workspace-topbar {
    display: flex;
  }
}

@media (min-width: 900px) {
  .workspace-topbar {
    display: none;
  }
}
</style>
