package com.floodshield.app.di

import android.content.Context
import androidx.room.Room
import com.floodshield.app.data.local.AppDatabase
import com.floodshield.app.data.local.dao.AlertDao
import com.floodshield.app.data.local.dao.RiskDao
import com.floodshield.app.data.local.dao.ShelterDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "floodshield.db"
        ).build()

    @Provides
    fun provideRiskDao(db: AppDatabase): RiskDao = db.riskDao()

    @Provides
    fun provideShelterDao(db: AppDatabase): ShelterDao = db.shelterDao()

    @Provides
    fun provideAlertDao(db: AppDatabase): AlertDao = db.alertDao()
}
