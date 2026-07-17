package com.floodshield.app.ui.theme

import androidx.compose.ui.graphics.Color

// 主色调 - 蓝色系 (防洪/水相关)
val Blue40 = Color(0xFF1565C0)
val Blue80 = Color(0xFF90CAF9)
val Blue90 = Color(0xFFBBDEFB)

// 辅助色 - 橙色系 (警告/紧急)
val Orange40 = Color(0xFFE65100)
val Orange80 = Color(0xFFFFCC80)

// 风险等级颜色 (5级体系)
val RiskNormal = Color(0xFF388E3C)       // 绿色 - 当前正常
val RiskAttention = Color(0xFFFFA000)    // 黄色 - 需要关注
val RiskHigh = Color(0xFFE65100)         // 橙色 - 高风险
val RiskCritical = Color(0xFFD32F2F)     // 红色 - 立即避险
val RiskUnknown = Color(0xFF757575)      // 灰色 - 数据不足

// 背景色
val BackgroundLight = Color(0xFFF5F5F5)
val BackgroundDark = Color(0xFF121212)
val SurfaceLight = Color(0xFFFFFFFF)
val SurfaceDark = Color(0xFF1E1E1E)
