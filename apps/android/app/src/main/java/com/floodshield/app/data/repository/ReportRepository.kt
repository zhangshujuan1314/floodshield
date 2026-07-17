package com.floodshield.app.data.repository

import com.floodshield.app.data.api.ApiService
import com.floodshield.app.data.api.CreateReportRequest
import com.floodshield.app.data.api.Report
import com.floodshield.app.data.api.Resource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReportRepository @Inject constructor(
    private val api: ApiService
) {
    /**
     * 提交险情上报。
     */
    fun submitReport(report: CreateReportRequest): Flow<Resource<Report>> = flow {
        emit(Resource.Loading)

        try {
            val response = api.submitReport(report)
            val data = response.data
            if (data != null) {
                emit(Resource.Success(data))
            } else {
                emit(Resource.Error("上报响应为空"))
            }
        } catch (e: Exception) {
            emit(Resource.Error(e.message ?: "上报失败", e))
        }
    }

    /**
     * 获取上报详情。
     */
    fun getReport(id: String): Flow<Resource<Report>> = flow {
        emit(Resource.Loading)

        try {
            val response = api.getReport(id)
            val data = response.data
            if (data != null) {
                emit(Resource.Success(data))
            } else {
                emit(Resource.Error("报告不存在"))
            }
        } catch (e: Exception) {
            emit(Resource.Error(e.message ?: "获取报告失败", e))
        }
    }
}
