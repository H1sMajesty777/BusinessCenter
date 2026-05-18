// frontend/src/components/ImageSlider.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { Building2 } from 'lucide-react';

const ImageSlider = ({ images, officeNumber, className = '', autoPlay = true }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [touchStart, setTouchStart] = useState(null);

  useEffect(() => {
    if (autoPlay && !isHovered && images?.length > 1) {
      const interval = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % images.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoPlay, isHovered, images?.length]);

  const goToPrev = useCallback((e) => {
    e?.stopPropagation();
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  }, [images?.length]);

  const goToNext = useCallback((e) => {
    e?.stopPropagation();
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  }, [images?.length]);

  const goToSlide = useCallback((index, e) => {
    e?.stopPropagation();
    setCurrentIndex(index);
  }, []);

  const handleTouchStart = (e) => {
    setTouchStart(e.touches[0].clientX);
  };

  const handleTouchEnd = (e) => {
    if (!touchStart) return;
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStart - touchEnd;
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        goToNext();
      } else {
        goToPrev();
      }
    }
    setTouchStart(null);
  };

  if (!images || images.length === 0) {
    return (
      <div 
        className={`image-slider ${className}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="slider-placeholder">
          <Building2 size={48} />
          <span>Нет фото</span>
        </div>
      </div>
    );
  }

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

  // Кастомные стрелки вместо lucide
  const PrevArrow = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 18L9 12L15 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const NextArrow = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  return (
    <div 
      className={`image-slider ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <div className="slider-container">
        <div 
          className="slider-track"
          style={{ transform: `translateX(-${currentIndex * 100}%)` }}
        >
          {images.map((img, idx) => (
            <div key={idx} className="slider-slide">
              {img.image_url || img.url ? (
                <img 
                  src={img.image_url || img.url} 
                  alt={`Офис ${officeNumber} - фото ${idx + 1}`}
                  loading="lazy"
                />
              ) : (
                <div className={`gradient-bg ${getGradientClass(img.color)}`}>
                  <Building2 size={56} />
                  <span className="gradient-label">Офис {officeNumber}</span>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {images.length > 1 && (
          <>
            <button 
              className="slider-arrow prev" 
              onClick={goToPrev} 
              aria-label="Предыдущее фото"
              style={{
                opacity: isHovered ? 1 : 0,
                visibility: isHovered ? 'visible' : 'hidden'
              }}
            >
              <PrevArrow />
            </button>
            <button 
              className="slider-arrow next" 
              onClick={goToNext} 
              aria-label="Следующее фото"
              style={{
                opacity: isHovered ? 1 : 0,
                visibility: isHovered ? 'visible' : 'hidden'
              }}
            >
              <NextArrow />
            </button>
          </>
        )}
      </div>
      
      {images.length > 1 && (
        <>
          <div className="slider-dots">
            {images.map((_, idx) => (
              <button
                key={idx}
                className={`slider-dot ${idx === currentIndex ? 'active' : ''}`}
                onClick={(e) => goToSlide(idx, e)}
                aria-label={`Перейти к фото ${idx + 1}`}
              />
            ))}
          </div>
          
          <div className="slider-counter">
            <span className="counter-icon"></span>
            <span>{currentIndex + 1} / {images.length}</span>
          </div>
        </>
      )}
    </div>
  );
};

export default ImageSlider;