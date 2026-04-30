// frontend/src/contexts/FavoritesContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { getFavorites, addFavorite, removeFavorite, checkFavorite } from '../services/favoritesService';

const FavoritesContext = createContext();

export const useFavorites = () => useContext(FavoritesContext);

export const FavoritesProvider = ({ children }) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  // Загрузка избранного с сервера при монтировании
  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const data = await getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Ошибка загрузки избранного:', error);
      setFavorites([]);
    } finally {
      setLoading(false);
    }
  };

  const addToFavorites = async (office) => {
    try {
      await addFavorite(office.id);
      setFavorites(prev => {
        if (prev.some(f => f.office_id === office.id)) return prev;
        // Сохраняем офис с нужными полями
        const favoriteOffice = {
          id: office.id,
          office_id: office.id,
          office_number: office.office_number,
          floor: office.floor,
          area_sqm: office.area_sqm,
          price_per_month: office.price_per_month,
          is_free: office.is_free
        };
        return [favoriteOffice, ...prev];
      });
    } catch (error) {
      console.error('Ошибка добавления в избранное:', error);
    }
  };

  const removeFromFavorites = async (officeId) => {
    try {
      await removeFavorite(officeId);
      setFavorites(prev => prev.filter(f => f.office_id !== officeId));
    } catch (error) {
      console.error('Ошибка удаления из избранного:', error);
    }
  };

  const isFavorite = async (officeId) => {
    try {
      return await checkFavorite(officeId);
    } catch (error) {
      console.error('Ошибка проверки избранного:', error);
      return false;
    }
  };

  const toggleFavorite = async (office) => {
    const isFav = favorites.some(f => f.office_id === office.id);
    if (isFav) {
      await removeFromFavorites(office.id);
    } else {
      await addToFavorites(office);
    }
  };

  return (
    <FavoritesContext.Provider value={{ 
      favorites, 
      loading,
      addToFavorites, 
      removeFromFavorites, 
      isFavorite: (officeId) => favorites.some(f => f.office_id === officeId),
      toggleFavorite,
      refreshFavorites: loadFavorites
    }}>
      {children}
    </FavoritesContext.Provider>
  );
};