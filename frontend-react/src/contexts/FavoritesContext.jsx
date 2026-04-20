import React, { createContext, useContext, useState, useEffect } from 'react';

const FavoritesContext = createContext();

export const useFavorites = () => useContext(FavoritesContext);

export const FavoritesProvider = ({ children }) => {
  const [favorites, setFavorites] = useState([]);

  // Загрузка избранного из localStorage при запуске
  useEffect(() => {
    const stored = localStorage.getItem('favorites');
    if (stored) {
      try {
        setFavorites(JSON.parse(stored));
      } catch (e) {
        console.error('Ошибка загрузки избранного:', e);
        setFavorites([]);
      }
    }
  }, []);

  // Сохранение в localStorage при изменении
  useEffect(() => {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }, [favorites]);

  const addToFavorites = (office) => {
    setFavorites(prev => {
      if (prev.some(f => f.id === office.id)) return prev;
      return [...prev, office];
    });
  };

  const removeFromFavorites = (officeId) => {
    setFavorites(prev => prev.filter(f => f.id !== officeId));
  };

  const isFavorite = (officeId) => {
    return favorites.some(f => f.id === officeId);
  };

  const toggleFavorite = (office) => {
    if (isFavorite(office.id)) {
      removeFromFavorites(office.id);
    } else {
      addToFavorites(office);
    }
  };

  return (
    <FavoritesContext.Provider value={{ 
      favorites, 
      addToFavorites, 
      removeFromFavorites, 
      isFavorite, 
      toggleFavorite 
    }}>
      {children}
    </FavoritesContext.Provider>
  );
};