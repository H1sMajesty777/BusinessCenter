// Мок-данные для изображений офисов
// Каждый офис имеет 3-4 градиентных изображения

export const officeImages = {
  1: [
    { type: 'gradient', color: 'gradient-1' },
    { type: 'gradient', color: 'gradient-2' },
    { type: 'gradient', color: 'gradient-3' },
  ],
  2: [
    { type: 'gradient', color: 'gradient-2' },
    { type: 'gradient', color: 'gradient-3' },
    { type: 'gradient', color: 'gradient-4' },
    { type: 'gradient', color: 'gradient-5' },
  ],
  3: [
    { type: 'gradient', color: 'gradient-3' },
    { type: 'gradient', color: 'gradient-4' },
    { type: 'gradient', color: 'gradient-5' },
  ],
  4: [
    { type: 'gradient', color: 'gradient-4' },
    { type: 'gradient', color: 'gradient-5' },
    { type: 'gradient', color: 'gradient-1' },
    { type: 'gradient', color: 'gradient-2' },
  ],
  5: [
    { type: 'gradient', color: 'gradient-5' },
    { type: 'gradient', color: 'gradient-1' },
    { type: 'gradient', color: 'gradient-2' },
    { type: 'gradient', color: 'gradient-3' },
  ],
  6: [
    { type: 'gradient', color: 'gradient-1' },
    { type: 'gradient', color: 'gradient-2' },
    { type: 'gradient', color: 'gradient-3' },
  ],
  7: [
    { type: 'gradient', color: 'gradient-2' },
    { type: 'gradient', color: 'gradient-3' },
    { type: 'gradient', color: 'gradient-4' },
  ],
  8: [
    { type: 'gradient', color: 'gradient-3' },
    { type: 'gradient', color: 'gradient-4' },
    { type: 'gradient', color: 'gradient-5' },
  ],
  9: [
    { type: 'gradient', color: 'gradient-4' },
    { type: 'gradient', color: 'gradient-5' },
    { type: 'gradient', color: 'gradient-1' },
  ],
  10: [
    { type: 'gradient', color: 'gradient-5' },
    { type: 'gradient', color: 'gradient-1' },
    { type: 'gradient', color: 'gradient-2' },
  ],
};

// Функция для получения изображений офиса
export const getOfficeImages = (officeId) => {
  return officeImages[officeId] || officeImages[1];
};