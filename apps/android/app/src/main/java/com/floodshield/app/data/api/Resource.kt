package com.floodshield.app.data.api

/**
 * 封装 API 调用状态的密封类。
 * 用于 Repository -> ViewModel -> UI 的数据流。
 */
sealed class Resource<out T> {
    /** 加载中 */
    data object Loading : Resource<Nothing>()

    /** 成功，携带数据 */
    data class Success<T>(val data: T) : Resource<T>()

    /** 失败，携带错误信息 */
    data class Error(
        val message: String,
        val cause: Throwable? = null
    ) : Resource<Nothing>()

    /** 是否为加载中状态 */
    val isLoading: Boolean get() = this is Loading

    /** 是否为成功状态 */
    val isSuccess: Boolean get() = this is Success

    /** 是否为错误状态 */
    val isError: Boolean get() = this is Error

    /**
     * 将 Resource 映射为新的数据类型。
     */
    inline fun <R> map(transform: (T) -> R): Resource<R> = when (this) {
        is Loading -> Loading
        is Success -> Success(transform(data))
        is Error -> Error(message, cause)
    }

    /**
     * 获取数据，失败时返回 null。
     */
    fun getOrNull(): T? = when (this) {
        is Success -> data
        else -> null
    }

    /**
     * 获取数据，失败时返回默认值。
     */
    fun getOrDefault(default: @UnsafeVariance T): T = when (this) {
        is Success -> data
        else -> default
    }
}
