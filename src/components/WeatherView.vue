<template>
  <div class="weather-main" style="position:relative;">
    <div class="weather-info"
         @mouseenter="showWeatherDetails"
         @mouseleave="hideWeatherDetails"
         @click="toggleWeatherDetails">
      <img :src="currentWeatherIcon" alt="天气图标" class="weather-icon" />
      <span class="weather-city">杭州市</span>
      <span class="weather-greeting">{{ greetingMessage }}</span>
    </div>
    <div :class="['weather-details', { show: showDetails }]">
      <table>
        <!-- ...表格内容... -->
            <thead>
            <tr>
                <th>日期</th>
                <th>白天天气</th>
                <th>白天温度</th>
                <th>白天风向</th>
                <th>白天风力</th>
                <th>夜晚天气</th>
                <th>夜晚温度</th>
                <th>夜晚风向</th>
                <th>夜晚风力</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="forecast in weatherForecasts" :key="forecast.date">
                <td>{{ forecast.date }}</td>
                <td><img :src="forecast.dayIcon" :alt="forecast.dayweather" class="weather-icon"></td>
                <td>{{ forecast.daytemp }}°C</td>
                <td>{{ forecast.daywind }}</td>
                <td>{{ forecast.daypower }}级</td>
                <td><img :src="forecast.nightIcon" :alt="forecast.nightweather" class="weather-icon"></td>
                <td>{{ forecast.nighttemp }}°C</td>
                <td>{{ forecast.nightwind }}</td>
                <td>{{ forecast.nightpower }}级</td>
            </tr>
            </tbody>
      </table>
      <div class="cancel-btn" @click="hideWeatherDetailsImmediately">
        <img :src="cancelIcon" alt="关闭" width="32" height="32" />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

// 逐个导入图片资源
import daybreakIcon from '@/assets/images/weather_icon/日出.png'
import sunsetIcon from '@/assets/images/weather_icon/日落.png'
import snowIcon from '@/assets/images/weather_icon/雪.png'
import nightCloudyIcon from '@/assets/images/weather_icon/夜多云.png'
import nightClearIcon from '@/assets/images/weather_icon/夜晴png.png'
import lightRainIcon from '@/assets/images/weather_icon/小雨.png'
import cloudyIcon from '@/assets/images/weather_icon/多云.png'
import rainIcon from '@/assets/images/weather_icon/雨.png'
import dustIcon from '@/assets/images/weather_icon/尘png.png'
import thunderIcon from '@/assets/images/weather_icon/雷.png'
import overcastIcon from '@/assets/images/weather_icon/阴.png'
import localSnowIcon from '@/assets/images/weather_icon/局部阵雪.png'
import hailIcon from '@/assets/images/weather_icon/强雪雹交加.png'
import clearIcon from '@/assets/images/weather_icon/晴.png'
import unknownIcon from '@/assets/images/weather_icon/未知.png'
import cancelIcon from '@/assets/images/weather_icon/cancel_dark.png'

const weatherIconMap = {
    日出: daybreakIcon,
    日落: sunsetIcon,
    雪: snowIcon,
    夜多云: nightCloudyIcon,
    夜晴: nightClearIcon,
    小雨: lightRainIcon,
    多云: cloudyIcon,
    雨: rainIcon,
    尘: dustIcon,
    雷: thunderIcon,
    阴: overcastIcon,
    局部阵雪: localSnowIcon,
    强雪雹交加: hailIcon,
    晴: clearIcon,
    未知: unknownIcon
}

export default {
    name: 'WeatherView',
    data () {
    return {
        weatherInfo: null,
        currentWeather: '',
        currentWind: '',
        currentPower: '',
        currentWeatherIcon: '',
        showDetails: false,
        weatherForecasts: [],
        isDaytime: this.checkDaytime(),
        isClicked: false,
        cancelIcon // 用于关闭按钮
    }
    },
    methods: {
    async fetchWeatherInfo () {
        try {
        const response = await axios.get(`${import.meta.env.VITE_APP_API_URL}/weather/api/get_weather`)
        // 打印结果调试
        console.log('Weather API Response:', response.data)
        const data = response.data
        this.weatherForecasts = data.forecasts.map(cast => ({
            ...cast,
            dayIcon: this.getWeatherIcon(cast.dayweather),
            nightIcon: this.getWeatherIcon(cast.nightweather)
        }))
        // 可选：设置当前天气为第一天
        this.weatherInfo = this.weatherForecasts[0]
        this.updateCurrentWeather()
    } catch (error) {
        console.error('Error fetching weather information:', error)
    }
    },
    getWeatherIcon(weather) {
        return weatherIconMap[weather] || unknownIcon;
    },
    updateCurrentWeather () {
        const currentHour = new Date().getHours()
        const currentMinute = new Date().getMinutes()
        const isDaytime = currentHour >= 6 && currentHour < 18

        if (currentHour >= 6 && currentHour < 18) {
        this.currentWeather = this.weatherInfo.dayweather
        this.currentWind = this.weatherInfo.daywind
        this.currentPower = this.weatherInfo.daypower
        } else {
        this.currentWeather = this.weatherInfo.nightweather
        this.currentWind = this.weatherInfo.nightwind
        this.currentPower = this.weatherInfo.nightpower
        }
        if (currentHour === 6 && currentMinute < 30) {
        this.currentWeatherIcon = weatherIconMap['日出']
        } else if (currentHour === 17 && currentMinute >= 30) {
        this.currentWeatherIcon = weatherIconMap['日落']
        } else if (this.currentWeather.includes('雷')) {
        this.currentWeatherIcon = weatherIconMap['雷']
        } else if (this.currentWeather.includes('雨')) {
        this.currentWeatherIcon = weatherIconMap['雨']
        } else if (this.currentWeather.includes('冰雹')) {
        this.currentWeatherIcon = weatherIconMap['强雪雹交加']
        } else if (this.currentWeather.includes('雪')) {
        this.currentWeatherIcon = weatherIconMap['雪']
        } else if (isDaytime && this.currentWeather.includes('晴')) {
        this.currentWeatherIcon = weatherIconMap['晴']
        } else if (!isDaytime && this.currentWeather.includes('晴')) {
        this.currentWeatherIcon = weatherIconMap['夜晴']
        } else if (!isDaytime && this.currentWeather.includes('多云')) {
        this.currentWeatherIcon = weatherIconMap['夜多云']
        } else {
        this.currentWeatherIcon = weatherIconMap[this.currentWeather] || unknownIcon
        }
    },
    showWeatherDetails () {
    this.showDetails = true
    },
    hideWeatherDetails () {
        if (!this.isClicked) {
        this.showDetails = false
        }
    },
    toggleWeatherDetails () {
        this.isClicked = !this.isClicked
        this.showDetails = this.isClicked
    },
    hideWeatherDetailsImmediately () {
        this.isClicked = false
        this.showDetails = false
    },
    checkDaytime () {
        const currentHour = new Date().getHours()
        return currentHour >= 6 && currentHour < 18
    }
    },
    computed: {
    greetingMessage () {
        const currentHour = new Date().getHours()
        let greeting = ''

        if (currentHour >= 5 && currentHour < 8) {
        greeting = '清晨好'
        } else if (currentHour >= 8 && currentHour < 12) {
        greeting = '早上好'
        } else if (currentHour >= 12 && currentHour < 14) {
        greeting = '中午好'
        } else if (currentHour >= 14 && currentHour < 18) {
        greeting = '下午好'
        } else if (currentHour >= 18 && currentHour < 20) {
        greeting = '傍晚好'
        } else if (currentHour >= 20 && currentHour < 23) {
        greeting = '晚上好'
        } else {
        greeting = '深夜好'
        }

        return `${greeting}${this.currentWeather}`
    }
    },
    mounted () {
    this.fetchWeatherInfo()
    }
}
</script>
    
<style>
.weather-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.weather-info {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: rgb(97, 144, 38);
  margin-bottom: 10px;
}
.weather-icon {
  width: 40px;
  height: 40px;
  margin-right: 10px;
}
.weather-city {
  margin-right: 10px;
}
.weather-greeting {
  margin-right: 10px;
}

.weather-details {
  position: absolute;
  top: 60px;
  left: 0;
  width: 400px;
  background: #fff;
  border: 1px solid #addfc2;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  border-radius: 10px;
  z-index: 1001;
  padding: 20px;
  display: none;
}
.weather-details.show {
  display: block;
}
.cancel-btn {
  display: flex;
  justify-content: center;
  margin-top: 10px;
  cursor: pointer;
}
</style>