<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-header">
          <div>
            <div class="budget-label">{{ t('restocking.budget') }}</div>
            <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
          </div>
          <div class="budget-hint">
            {{ t('restocking.fullNeed', { amount: formatCurrency(fullNeedTotal, currentCurrency) }) }}
          </div>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          :step="BUDGET_STEP"
          v-model.number="budget"
          :disabled="refreshing"
          @change="loadRecommendations"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ formatCurrency(selectedTotal, currentCurrency) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(budget - selectedTotal, currentCurrency) }}</div>
        </div>
        <div :class="['stat-card', unfunded.length ? 'danger' : 'info']">
          <div class="stat-label">{{ t('restocking.itemsFunded') }}</div>
          <div class="stat-value">{{ selectedCount }} / {{ recommendations.length + unfunded.length }}</div>
        </div>
      </div>

      <div v-if="successOrder" class="notice notice-success">
        <strong>{{ t('restocking.orderPlaced', { orderNumber: successOrder.order_number }) }}</strong>
        <span>
          {{ t('restocking.orderPlacedDetail', {
            count: successOrder.items.length,
            total: formatCurrency(successOrder.total_value, currentCurrency),
            days: successOrder.lead_time_days,
            date: formatDate(successOrder.expected_delivery)
          }) }}
        </span>
        <router-link to="/orders" class="notice-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="notice notice-error">
        <strong>{{ t('restocking.orderFailed') }}</strong>
        <span>{{ submitError }}</span>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button class="order-button" :disabled="!canSubmit" @click="placeOrder">
            {{ submitting
              ? t('restocking.placing')
              : t('restocking.placeOrder', { count: selectedCount, total: formatCurrency(selectedTotal, currentCurrency) }) }}
          </button>
        </div>
        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-check">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :disabled="recommendations.length === 0"
                    :title="t('restocking.selectAll')"
                    @change="toggleAll"
                  />
                </th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.forecast') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.priority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="recommendations.length === 0">
                <td colspan="11" class="empty-row">{{ t('restocking.noRecommendations') }}</td>
              </tr>
              <tr
                v-for="rec in recommendations"
                :key="rec.sku"
                :class="{ unselected: !selected.has(rec.sku) }"
              >
                <td class="col-check">
                  <input type="checkbox" :checked="selected.has(rec.sku)" @change="toggle(rec.sku)" />
                </td>
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>{{ translateWarehouse(rec.warehouse) }}</td>
                <td>
                  {{ rec.quantity_on_hand }} / {{ rec.reorder_point }}
                  <span v-if="rec.on_order" class="on-order">+{{ rec.on_order }}</span>
                </td>
                <td>
                  {{ rec.forecasted_demand }}
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
                <td>
                  <strong>{{ rec.quantity }}</strong>
                  <span v-if="rec.is_partial" class="badge warning partial-badge">{{ t('restocking.partial') }}</span>
                </td>
                <td>{{ formatCurrencyWithDecimals(rec.unit_cost, currentCurrency, 2) }}</td>
                <td><strong>{{ formatCurrency(rec.line_total, currentCurrency) }}</strong></td>
                <td>{{ t('common.days', { count: rec.lead_time_days }) }}</td>
                <td>
                  <span :class="['badge', rec.priority]">{{ t(`priority.${rec.priority}`) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="unfunded.length" class="footnote">
          {{ t('restocking.unfunded', { count: unfunded.length }) }}:
          <span class="footnote-skus">{{ unfunded.map(u => u.sku).join(', ') }}</span>
        </div>
        <div v-if="sufficientCount" class="footnote">
          {{ t('restocking.sufficientStock', { count: sufficientCount }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Slider granularity in USD. Amounts stay in USD internally; only display converts.
const BUDGET_STEP = 1000
// The slider max is rounded up to this so a full restock is always reachable.
const BUDGET_MAX_ROUNDING = 25000

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName, translateWarehouse } = useI18n()
    const { selectedLocation, selectedCategory } = useFilters()

    const loading = ref(true)
    const refreshing = ref(false)
    const error = ref(null)

    const budget = ref(0)
    const maxBudget = ref(BUDGET_MAX_ROUNDING)
    const fullNeedTotal = ref(0)
    const recommendations = ref([])
    const unfunded = ref([])
    const sufficientCount = ref(0)

    // Set of SKUs the user wants to include in the order
    const selected = ref(new Set())

    const submitting = ref(false)
    const submitError = ref(null)
    const successOrder = ref(null)

    const currentFilters = () => ({
      warehouse: selectedLocation.value,
      category: selectedCategory.value
    })

    // Fetch the unconstrained need to size the slider, then fetch for the
    // current budget. Called on mount, on filter change and after an order
    // (orders count as on-order stock, so the full need shrinks).
    const initialize = async (resetBudget) => {
      const full = await api.getRestockingRecommendations({ budget: null, ...currentFilters() })
      fullNeedTotal.value = full.full_need_total
      maxBudget.value = Math.max(
        BUDGET_MAX_ROUNDING,
        Math.ceil(full.full_need_total / BUDGET_MAX_ROUNDING) * BUDGET_MAX_ROUNDING
      )
      if (resetBudget) {
        budget.value = Math.round(maxBudget.value / 2 / BUDGET_STEP) * BUDGET_STEP
      } else {
        budget.value = Math.min(budget.value, maxBudget.value)
      }
      await loadRecommendations()
    }

    const loadRecommendations = async () => {
      try {
        refreshing.value = true
        submitError.value = null
        const data = await api.getRestockingRecommendations({ budget: budget.value, ...currentFilters() })
        recommendations.value = data.items
        unfunded.value = data.unfunded
        sufficientCount.value = data.sufficient_count
        // Default to ordering everything the budget can fund
        selected.value = new Set(data.items.map(item => item.sku))
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        refreshing.value = false
      }
    }

    const load = async (resetBudget) => {
      try {
        loading.value = true
        error.value = null
        await initialize(resetBudget)
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Warehouse/category filters change which inventory can be restocked;
    // period and status filters have no meaning here (same as Inventory).
    watch([selectedLocation, selectedCategory], () => {
      successOrder.value = null
      load(true)
    })

    const selectedLines = computed(() =>
      recommendations.value.filter(rec => selected.value.has(rec.sku))
    )
    const selectedCount = computed(() => selectedLines.value.length)
    const selectedTotal = computed(() =>
      Math.round(selectedLines.value.reduce((sum, rec) => sum + rec.line_total, 0) * 100) / 100
    )
    const allSelected = computed(() =>
      recommendations.value.length > 0 && selectedCount.value === recommendations.value.length
    )
    const canSubmit = computed(() => selectedCount.value > 0 && !submitting.value && !refreshing.value)

    // Replace the Set instead of mutating it so Vue picks up the change
    const toggle = (sku) => {
      const next = new Set(selected.value)
      if (next.has(sku)) next.delete(sku)
      else next.add(sku)
      selected.value = next
    }

    const toggleAll = () => {
      selected.value = allSelected.value
        ? new Set()
        : new Set(recommendations.value.map(rec => rec.sku))
    }

    const placeOrder = async () => {
      if (!canSubmit.value) return
      try {
        submitting.value = true
        submitError.value = null
        successOrder.value = null
        const order = await api.createRestockingOrder({
          budget: budget.value,
          items: selectedLines.value.map(rec => ({ sku: rec.sku, quantity: rec.quantity }))
        })
        successOrder.value = order
        // Ordered units now count as on-order stock, so refresh the list
        await initialize(false)
      } catch (err) {
        submitError.value = err.response?.data?.detail || err.message
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateString) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    onMounted(() => load(true))

    return {
      t,
      currentCurrency,
      translateProductName,
      translateWarehouse,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate,
      BUDGET_STEP,
      loading,
      refreshing,
      error,
      budget,
      maxBudget,
      fullNeedTotal,
      recommendations,
      unfunded,
      sufficientCount,
      selected,
      selectedCount,
      selectedTotal,
      allSelected,
      canSubmit,
      toggle,
      toggleAll,
      submitting,
      submitError,
      successOrder,
      placeOrder,
      loadRecommendations
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.budget-hint {
  font-size: 0.875rem;
  color: #64748b;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-slider:disabled {
  cursor: wait;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.notice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.notice-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.notice-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.notice-link {
  margin-left: auto;
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
}

.notice-link:hover {
  text-decoration: underline;
}

.order-button {
  padding: 0.5rem 1.25rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.order-button:hover:not(:disabled) {
  background: #2563eb;
}

.order-button:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.restock-table .col-check {
  width: 40px;
  text-align: center;
}

.restock-table input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.restock-table tr.unselected td {
  color: #94a3b8;
}

.restock-table tr.unselected td strong {
  color: #94a3b8;
}

.restock-table .badge {
  margin-left: 0.4rem;
}

.partial-badge {
  font-size: 0.65rem;
}

.on-order {
  margin-left: 0.3rem;
  font-size: 0.75rem;
  color: #2563eb;
}

.empty-row {
  text-align: center;
  color: #64748b;
  padding: 2rem !important;
}

.footnote {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  font-size: 0.85rem;
  color: #64748b;
}

.footnote-skus {
  color: #0f172a;
  font-weight: 500;
}
</style>
