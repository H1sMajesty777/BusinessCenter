import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Building2 } from 'lucide-react';

const ImageSlider = ({ images, officeNumber, className = '' }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Если нет изображений — показываем заглушку с иконкой
  if (!images || images.length === 0) {
    return (
      <div className={`image-slider ${className}`}>
        <div className="slider-placeholder">
          <Building2 size={48} />
          <span>Нет фото</span>
        </div>
      </div>
    );
  }

  const goToPrev = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const goToNext = (e) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const goToSlide = (index, e) => {
    e.stopPropagation();
    setCurrentIndex(index);
  };

  // Получаем цвет для градиента
  const getGradientClass = (colorName) => {
    const gradients = {
      'gradient-1': 'gradient-1',
      'gradient-2': 'gradient-2',
      'gradient-3': 'gradient-3',
      'gradient-4': 'gradient-4',
      'gradient-5': 'gradient-5',
      'gradient-6': 'gradient-6',
    };
    return gradients[colorName] || 'gradient-1';
  };

  return (
    <div className={`image-slider ${className}`}>
      <div className="slider-container">
        <div 
          className="slider-track"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {images.map((img, idx) => (
            <div key={idx} className="slider-slide">
              {img.url ? (
                <img src={img.url} alt={`Офис ${officeNumber}`} />
              ) : (
                <div className={`gradient-bg ${getGradientClass(img.color)}`}>
                  <Building2 size={64} />
                  <span className="gradient-label">Офис {officeNumber}</span>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {images.length > 1 && (
          <>
            <button className="slider-arrow prev" onClick={goToPrev}>
              <ChevronLeft size={20} />
            </button>
            <button className="slider-arrow next" onClick={goToNext}>
              <ChevronRight size={20} />
            </button>
          </>
        )}
      </div>
      
      {images.length > 1 && (
        <div className="slider-dots">
          {images.map((_, idx) => (
            <button
              key={idx}
              className={`slider-dot ${idx === currentIndex ? 'active' : ''}`}
              onClick={(e) => goToSlide(idx, e)}
            />
          ))}
        </div>
      )}
      
      <div className="slider-counter">
        {currentIndex + 1} / {images.length}
      </div>
    </div>
  );
};

export default ImageSlider;