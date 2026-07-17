package com.floodshield.app.util

import android.content.Context
import android.widget.Toast
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

fun Context.showToast(message: String, duration: Int = Toast.LENGTH_SHORT) {
    Toast.makeText(this, message, duration).show()
}

fun <T> Flow<Result<T>>.handleResult(
    onSuccess: (T) -> Unit,
    onError: (Throwable) -> Unit
): Flow<Result<T>> {
    return this.map { result ->
        result.fold(
            onSuccess = {
                onSuccess(it)
                Result.success(it)
            },
            onFailure = {
                onError(it)
                Result.failure(it)
            }
        )
    }
}
