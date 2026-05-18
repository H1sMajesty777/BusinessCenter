// frontend/src/utils/featureMapping.js

/**
 * Маппинг признаков ML модели в понятные человеку названия
 * Основан на feature_extractor.py
 */

export const FEATURE_MAPPING = {
  // Базовые характеристики офиса
  floor: { name: 'Этаж', icon: '', description: 'Номер этажа расположения офиса', unit: '' },
  area_sqm: { name: 'Площадь', icon: '', description: 'Общая площадь офисного помещения', unit: 'м²' },
  price_per_month: { name: 'Цена за месяц', icon: '', description: 'Стоимость аренды в месяц', unit: '₽' },
  price_per_sqm: { name: 'Цена за м²', icon: '', description: 'Стоимость квадратного метра', unit: '₽' },
  is_free: { name: 'Статус', icon: '', description: 'Свободен / Арендован', unit: '' },
  
  // Просмотры
  total_views: { name: 'Всего просмотров', icon: '', description: 'Общее количество просмотров за всё время', unit: '' },
  unique_viewers: { name: 'Уникальных просмотров', icon: '', description: 'Количество уникальных пользователей', unit: '' },
  avg_view_duration: { name: 'Средняя длительность', icon: '⏱', description: 'Среднее время просмотра офиса', unit: 'сек' },
  contact_rate: { name: 'Конверсия в контакт', icon: '', description: 'Доля просмотров, завершившихся контактом', unit: '%' },
  views_7d: { name: 'Просмотров за 7 дней', icon: '', description: 'Активность за последнюю неделю', unit: '' },
  views_30d: { name: 'Просмотров за 30 дней', icon: '', description: 'Активность за последний месяц', unit: '' },
  views_90d: { name: 'Просмотров за 90 дней', icon: '', description: 'Активность за последний квартал', unit: '' },
  views_trend_30_90d: { name: 'Тренд просмотров', icon: '', description: 'Изменение активности по сравнению с прошлым периодом', unit: '%' },
  
  // Заявки
  total_apps: { name: 'Всего заявок', icon: '', description: 'Общее количество заявок на офис', unit: '' },
  approval_rate: { name: 'Процент одобрения', icon: '', description: 'Доля одобренных заявок', unit: '%' },
  days_since_last_app: { name: 'Давность последней заявки', icon: '', description: 'Сколько дней назад была последняя заявка', unit: 'дн.' },
  
  // Договоры
  total_contracts: { name: 'Всего договоров', icon: '', description: 'Количество заключённых договоров', unit: '' },
  avg_contract_amount: { name: 'Средняя сумма договора', icon: '', description: 'Средняя стоимость аренды по договорам', unit: '₽' },
  active_contracts: { name: 'Активных договоров', icon: '', description: 'Количество действующих договоров', unit: '' },
  
  // Конкуренция
  competition_ratio: { name: 'Конкуренция на этаже', icon: '', description: 'Доля свободных офисов на этаже', unit: '%' },
  avg_price_on_floor: { name: 'Средняя цена на этаже', icon: '', description: 'Рыночная цена на этаже', unit: '₽' },
  price_competition_ratio: { name: 'Ценовой индекс', icon: '', description: 'Отношение цены офиса к средней по этажу', unit: '' },
  free_on_floor: { name: 'Свободных на этаже', icon: '', description: 'Количество свободных офисов на этаже', unit: '' },
  
  // Составные
  popularity_score: { name: 'Популярность', icon: '', description: 'Просмотров в день с момента создания', unit: '' },
  office_age_days: { name: 'Возраст офиса', icon: '', description: 'Дней с момента создания', unit: 'дн.' }
};

/**
 * Получить информацию о признаке по его имени
 * @param {string} featureName - Название признака (например, 'total_views')
 * @returns {object} - Объект с name, icon, description, unit
 */
export const getFeatureInfo = (featureName) => {
  if (!featureName) {
    return { name: 'Неизвестно', icon: '????', description: '', unit: '' };
  }
  
  // Прямое совпадение
  if (FEATURE_MAPPING[featureName]) {
    return FEATURE_MAPPING[featureName];
  }
  
  // Пытаемся найти частичное совпадение (для случаев feature_19)
  const lowerName = featureName.toLowerCase();
  for (const [key, value] of Object.entries(FEATURE_MAPPING)) {
    if (lowerName.includes(key.toLowerCase()) || key.toLowerCase().includes(lowerName)) {
      return value;
    }
  }
  
  // Для числовых индексов (feature_0, feature_1 и т.д.)
  const match = featureName.match(/feature_(\d+)/);
  if (match) {
    const index = parseInt(match[1]);
    const indexMapping = {
      0: 'floor', 1: 'area_sqm', 2: 'price_per_month', 3: 'price_per_sqm', 4: 'is_free',
      5: 'total_views', 6: 'unique_viewers', 7: 'avg_view_duration', 8: 'contact_rate',
      9: 'views_7d', 10: 'views_30d', 11: 'views_90d', 12: 'views_trend_30_90d',
      13: 'total_apps', 14: 'approval_rate', 15: 'days_since_last_app',
      16: 'total_contracts', 17: 'avg_contract_amount', 18: 'active_contracts',
      19: 'competition_ratio', 20: 'avg_price_on_floor', 21: 'price_competition_ratio',
      22: 'popularity_score', 23: 'office_age_days'
    };
    const mappedKey = indexMapping[index];
    if (mappedKey && FEATURE_MAPPING[mappedKey]) {
      return FEATURE_MAPPING[mappedKey];
    }
  }
  
  return { name: featureName, icon: '🔬', description: 'Технический признак модели', unit: '' };
};

/**
 * Форматирует значение признака с единицей измерения
 */
export const formatFeatureValue = (featureName, value) => {
  const info = getFeatureInfo(featureName);
  if (info.unit === '%') {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (info.unit === '₽') {
    return `${Math.round(value).toLocaleString()} ₽`;
  }
  if (info.unit === 'м²') {
    return `${Math.round(value)} м²`;
  }
  if (typeof value === 'number') {
    return value.toFixed(1);
  }
  return value;
};