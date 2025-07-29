import React, { createContext, useContext, useReducer, useEffect } from 'react';

// Initial state
const initialState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  devices: [],
  dashboardData: null,
  loading: false,
  error: null,
};

// Action types
export const ACTION_TYPES = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_DEVICES: 'SET_DEVICES',
  ADD_DEVICE: 'ADD_DEVICE',
  UPDATE_DEVICE: 'UPDATE_DEVICE',
  DELETE_DEVICE: 'DELETE_DEVICE',
  SET_DASHBOARD_DATA: 'SET_DASHBOARD_DATA',
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case ACTION_TYPES.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case ACTION_TYPES.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    case ACTION_TYPES.CLEAR_ERROR:
      return { ...state, error: null };
    
    case ACTION_TYPES.LOGIN_SUCCESS:
      localStorage.setItem('token', action.payload.token);
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        error: null,
      };
    
    case ACTION_TYPES.LOGOUT:
      localStorage.removeItem('token');
      return {
        ...initialState,
        token: null,
        isAuthenticated: false,
      };
    
    case ACTION_TYPES.SET_DEVICES:
      return { ...state, devices: action.payload };
    
    case ACTION_TYPES.ADD_DEVICE:
      return { ...state, devices: [...state.devices, action.payload] };
    
    case ACTION_TYPES.UPDATE_DEVICE:
      return {
        ...state,
        devices: state.devices.map(device =>
          device.id === action.payload.id ? { ...device, ...action.payload } : device
        ),
      };
    
    case ACTION_TYPES.DELETE_DEVICE:
      return {
        ...state,
        devices: state.devices.filter(device => device.id !== action.payload),
      };
    
    case ACTION_TYPES.SET_DASHBOARD_DATA:
      return { ...state, dashboardData: action.payload };
    
    default:
      return state;
  }
};

// Context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Auto-logout on token expiration
  useEffect(() => {
    if (state.token) {
      try {
        const payload = JSON.parse(atob(state.token.split('.')[1]));
        const expiry = payload.exp * 1000;
        
        if (Date.now() > expiry) {
          dispatch({ type: ACTION_TYPES.LOGOUT });
        } else {
          const timeout = setTimeout(() => {
            dispatch({ type: ACTION_TYPES.LOGOUT });
          }, expiry - Date.now());
          
          return () => clearTimeout(timeout);
        }
      } catch (error) {
        dispatch({ type: ACTION_TYPES.LOGOUT });
      }
    }
  }, [state.token]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
