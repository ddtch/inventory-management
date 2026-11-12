<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="monthlyData.length === 0" class="loading">{{ t('reports.noData') }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ formatMoney(q.total_revenue) }}</td>
                <td>{{ formatMoney(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend.title') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="row in monthlyRows" :key="row.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: row.barHeight + 'px' }"
                  :title="formatMoney(row.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ row.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth.title') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.monthOverMonth.month') }}</th>
                <th>{{ t('reports.monthOverMonth.orders') }}</th>
                <th>{{ t('reports.monthOverMonth.revenue') }}</th>
                <th>{{ t('reports.monthOverMonth.change') }}</th>
                <th>{{ t('reports.monthOverMonth.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthlyRows" :key="row.month">
                <td><strong>{{ row.label }}</strong></td>
                <td>{{ row.order_count }}</td>
                <td>{{ formatMoney(row.revenue) }}</td>
                <td>
                  <span v-if="row.change !== null" :class="row.changeClass">{{ row.changeText }}</span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="row.change !== null" :class="row.changeClass">{{ row.growthText }}</span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrders') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
const MAX_BAR_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        error.value = t('reports.loadError')
        console.error('Failed to load reports:', err)
      } finally {
        loading.value = false
      }
    }

    const formatMoney = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    // Convert 'YYYY-MM' to a localized "Mon YYYY" label. The string comes from the
    // API, so validate it before splitting and fall back to the raw value.
    const formatMonth = (monthStr) => {
      const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(monthStr || '')
      if (!match) return monthStr
      return `${t('months.' + MONTH_KEYS[Number(match[2]) - 1])} ${match[1]}`
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )

    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (!best || q.total_revenue > best.total_revenue) best = q
      }
      return best ? best.quarter : ''
    })

    // Computed once instead of rescanning the array for every bar
    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
    )

    // One precomputed row per month, shared by the chart and the comparison table
    const monthlyRows = computed(() =>
      monthlyData.value.map((m, i) => {
        const row = {
          ...m,
          label: formatMonth(m.month),
          barHeight: maxRevenue.value > 0 ? (m.revenue / maxRevenue.value) * MAX_BAR_HEIGHT : 0,
          change: null,
          changeText: '',
          growthText: '',
          changeClass: ''
        }

        // The first month has no previous month to compare against
        if (i > 0) {
          const prev = monthlyData.value[i - 1].revenue
          const change = m.revenue - prev
          row.change = change
          row.changeClass = change > 0 ? 'positive-change' : change < 0 ? 'negative-change' : ''
          const sign = change > 0 ? '+' : change < 0 ? '-' : ''
          row.changeText = sign + formatMoney(Math.abs(change))
          // Growth is undefined when the previous month had zero revenue
          if (prev === 0) {
            row.growthText = t('reports.monthOverMonth.notAvailable')
          } else {
            const rate = (change / prev) * 100
            row.growthText = (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
          }
        }
        return row
      })
    )

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], loadData)

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      formatMoney,
      getFulfillmentClass
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

/* Warm retint — matches global card surface */
.card {
  background: var(--surface, #f7f3ec);
  border-radius: 14px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--hairline, #e2d8c8);
  box-shadow: none;
}

.card-header {
  margin-bottom: 1.5rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--hairline, #e2d8c8);
}

.card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--ink, #1c1914);
  margin: 0;
  letter-spacing: -0.015em;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: var(--canvas, #efe8dc);
  padding: 0.625rem 0.75rem;
  text-align: left;
  font-weight: 700;
  color: var(--muted, #6f6558);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  border-bottom: 1px solid var(--hairline, #e2d8c8);
}

.reports-table td {
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--hairline, #e2d8c8);
  color: var(--ink, #1c1914);
  font-size: 0.875rem;
}

.reports-table tr:hover {
  background: var(--canvas, #efe8dc);
}

.chart-container {
  padding: 2rem 1rem;
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: 0.5rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

/* Copper bar gradient */
.bar {
  width: 100%;
  background: linear-gradient(to top, var(--copper, #d06a2b), #e8895a);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: linear-gradient(to top, #b8591f, var(--copper, #d06a2b));
}

.bar-label {
  font-size: 0.75rem;
  color: var(--muted, #6f6558);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: 1.5rem;
}

/* Stats grid — warm retint */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.stat-card {
  background: var(--surface, #f7f3ec);
  border-radius: 14px;
  padding: 1.5rem;
  border: 1px solid var(--hairline, #e2d8c8);
  border-left: 4px solid var(--copper, #d06a2b);
  box-shadow: none;
}

.stat-label {
  font-size: 0.8125rem;
  color: var(--muted, #6f6558);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-family: 'Fraunces', serif;
  font-size: 1.875rem;
  font-weight: 600;
  color: var(--ink, #1c1914);
  letter-spacing: -0.02em;
}

/* Keep badge names matching global — these are overrides for pill shape */
.badge {
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge.success { background: #cee8d8; color: #1a5934; }
.badge.warning  { background: #f2dfc0; color: #733b0e; }
.badge.danger   { background: #f2d0d0; color: #851c1c; }

.positive-change {
  color: #276640;
  font-weight: 700;
}

.negative-change {
  color: #a52020;
  font-weight: 700;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--muted, #6f6558);
}

.error {
  background: #f9eaea;
  border: 1px solid #e0b0b0;
  color: #851c1c;
  padding: 1rem;
  border-radius: 10px;
  margin: 1rem 0;
}
</style>
