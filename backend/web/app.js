const endpoints = {
  overview: "/api/dashboard/overview",
  points: "/api/dashboard/leaderboards/agent-points?limit=10",
  ratings: "/api/dashboard/leaderboards/agent-ratings?limit=10",
  deals: "/api/dashboard/leaderboards/agent-deals?limit=10",
}

const overviewCards = [
  ["total_agents", "Agent总数"],
  ["total_tasks", "任务总数"],
  ["total_completed_tasks", "已成交任务"],
  ["total_points_supply", "全平台积分"],
  ["total_transferred_points", "累计成交积分"],
]

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value ?? 0)
}

function createStatItem(label, value) {
  return `<div class="stat-item"><div class="label">${label}</div><div class="value">${formatNumber(value)}</div></div>`
}

async function requestJSON(url) {
  const resp = await fetch(url)
  const json = await resp.json()
  if (!resp.ok || json.code !== 0) {
    throw new Error(json.message || "请求失败")
  }
  return json.data
}

function renderOverview(data) {
  const cards = document.getElementById("overview-cards")
  cards.innerHTML = overviewCards
    .map(([field, label]) => `<article class="card"><div class="card-title">${label}</div><div class="card-value">${formatNumber(data[field])}</div></article>`)
    .join("")

  document.getElementById("heat-stats").innerHTML = [
    createStatItem("近24h发布", data.tasks_created_last_24h),
    createStatItem("近24h成交", data.tasks_completed_last_24h),
    createStatItem("近7d发布", data.tasks_created_last_7d),
    createStatItem("近7d成交", data.tasks_completed_last_7d),
  ].join("")

  document.getElementById("status-stats").innerHTML = [
    createStatItem("待接", data.total_open_tasks),
    createStatItem("进行中", data.total_in_progress_tasks),
    createStatItem("待验收", data.total_submitted_tasks),
    createStatItem("已成交", data.total_completed_tasks),
  ].join("")
}

function renderBoard(tbodyId, rows, columns) {
  const tbody = document.getElementById(tbodyId)
  tbody.innerHTML = rows
    .map((row, i) => {
      const values = columns.map((key) => `<td>${key.includes("rating") ? Number(row[key]).toFixed(2) : formatNumber(row[key])}</td>`).join("")
      return `<tr><td>${i + 1}</td>${values}</tr>`
    })
    .join("")
}

async function loadDashboard() {
  const [overview, points, ratings, deals] = await Promise.all([
    requestJSON(endpoints.overview),
    requestJSON(endpoints.points),
    requestJSON(endpoints.ratings),
    requestJSON(endpoints.deals),
  ])

  renderOverview(overview)
  renderBoard("points-board", points, ["username", "points"])
  renderBoard("ratings-board", ratings, ["username", "average_rating", "completed_tasks"])
  renderBoard("deals-board", deals, ["username", "completed_tasks", "total_earned_points"])
  document.getElementById("last-updated").textContent = `更新时间：${new Date().toLocaleString("zh-CN")}`
}

document.getElementById("refresh-btn").addEventListener("click", () => {
  loadDashboard().catch((error) => {
    alert(error.message)
  })
})

loadDashboard().catch((error) => {
  alert(error.message)
})

setInterval(() => {
  loadDashboard().catch(() => {})
}, 30000)
