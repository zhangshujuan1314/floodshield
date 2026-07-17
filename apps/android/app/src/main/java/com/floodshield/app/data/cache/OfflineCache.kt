package com.floodshield.app.data.cache

/**
 * 离线缓存策略管理。
 *
 * 缓存策略：API 优先，失败时回退到 Room 缓存。
 * - 风险数据：5 分钟 TTL
 * - 避难所数据：1 小时 TTL
 * - 预警数据：5 分钟 TTL
 */
object OfflineCache {
    const val RISK_TTL_MS = 5 * 60 * 1000L      // 5 分钟
    const val SHELTER_TTL_MS = 60 * 60 * 1000L   // 1 小时
    const val ALERT_TTL_MS = 5 * 60 * 1000L      // 5 分钟

    /**
     * 检查缓存是否过期。
     */
    fun isExpired(cachedAt: Long, ttlMs: Long): Boolean {
        return System.currentTimeMillis() - cachedAt > ttlMs
    }

    /**
     * 获取过期阈值时间戳。
     * 用于批量删除过期缓存。
     */
    fun expiryThreshold(ttlMs: Long): Long {
        return System.currentTimeMillis() - ttlMs
    }
}
