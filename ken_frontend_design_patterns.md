# Ken Frontend Design Patterns

This document outlines the key design patterns, architectural decisions, and coding conventions used in the Ken Frontend application. It is written to serve as a reference for LLMs and developers to understand and consistently follow the existing patterns when working with and extending the codebase.

## Table of Contents

1. [State Management Patterns](#state-management-patterns)
2. [Component Architecture Patterns](#component-architecture-patterns)
3. [API Integration Patterns](#api-integration-patterns)
4. [Code Organization Patterns](#code-organization-patterns)
5. [Feature Flag Patterns](#feature-flag-patterns)
6. [Styling Patterns](#styling-patterns)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Routing Patterns](#routing-patterns)

---

## State Management Patterns

### Redux Toolkit Architecture

The application uses Redux Toolkit for state management, with specific patterns to ensure consistency and maintainability.

#### Slice Pattern

Redux state is organized into "slices" using Redux Toolkit's `createSlice`. Each slice:
- Has a unique name as identifier
- Contains its own reducer logic
- Defines related actions and selectors
- Manages a specific domain of the application state

```javascript
// Example pattern for creating a slice
const sliceName = 'businessContextsForecast';

const initialState = {
  data: {},
  loading: false,
  error: null,
};

const forecastSlice = createSlice({
  name: sliceName,
  initialState,
  reducers: {
    // Synchronous actions...
  },
  extraReducers: builder => {
    // Async actions handling...
  },
});
```

#### Selectors Pattern

State access is done through selectors created with `createDraftSafeSelector` to optimize component rendering.

```javascript
// Selector pattern example
export const selectForecastState = state => state[SLICE_NAME];

export const selectForecastData = createDraftSafeSelector(
  [selectForecastState], 
  forecastState => forecastState.data
);
```

#### Thunk Pattern for API Calls

API interactions are handled through asynchronous thunks created with `createApiThunk`, a custom wrapper around Redux Toolkit's `createAsyncThunk`. This abstracts away repetitive API handling code.

```javascript
// API thunk pattern
export const fetchResourceCostData = createApiThunk(
  `${SLICE_NAME}/fetchResourceCost`,
  getCloudResourceCost
);
```

### Dynamic Reducer Injection

The application uses a dynamic reducer injection pattern to:
- Load reducers only when needed (code splitting)
- Keep the main bundle size smaller
- Enable modular feature development

```javascript
// Class-based HOC pattern
const withReducerInjector = ({ key, reducer }) => WrappedComponent => {
  class ReducerInjector extends React.Component {
    constructor(props, context) {
      super(props, context);
      getInjectors(context.store).injectReducer(key, reducer);
    }
    render() {
      return <WrappedComponent {...this.props} />;
    }
  }
  return hoistNonReactStatics(ReducerInjector, WrappedComponent);
};

// Hook-based pattern
const useInjectReducer = ({ key, reducer }) => {
  const context = React.useContext(ReactReduxContext);
  React.useEffect(() => {
    getInjectors(context.store).injectReducer(key, reducer);
  }, []);
};
```

## Component Architecture Patterns

### Container/Presentational Pattern

The application follows a container/presentational pattern to separate concerns:

#### Container Components
- Connect to Redux state
- Handle data fetching logic
- Manage component state
- Pass data and callbacks to presentational components
- Usually located in `containers/` directory

```javascript
// Container component pattern
function ForecastPage() {
  const dispatch = useDispatch();
  const data = useSelector(selectForecastData);
  const loading = useSelector(selectForecastLoading);
  
  const handleSubmit = () => {
    dispatch(fetchData());
  };
  
  return (
    <ForecastChart 
      data={data}
      loading={loading}
      onSubmit={handleSubmit}
    />
  );
}

export default compose(
  injectReducer({ key: SLICE_NAME, reducer })
)(ForecastPage);
```

#### Presentational Components
- Focus on UI rendering
- Receive data via props
- Call callbacks passed through props
- Can have their own UI state, but no data fetching
- Usually located in `components/` directory

```javascript
// Presentational component pattern
function ForecastChart({ forecastData, analysisData }) {
  // UI rendering logic here
  return (
    <ChartWrapper>
      <ReactECharts option={chartOption} />
    </ChartWrapper>
  );
}
```

### Hooks Pattern

Custom hooks are used to encapsulate reusable logic:

```javascript
// Custom hook pattern
export const useConfigCatFlag = (flag = '', addLoading = false, key = null, currentUserData = null) => {
  useInjectReducer({ key: 'global', reducer: globalReducer });
  
  // Hook implementation...
  
  return addLoading ? [isLoading, enabledFlag] : enabledFlag;
};
```

## API Integration Patterns

### Axios Configuration Pattern

API requests are centralized through a configured Axios instance with interceptors:

```javascript
// Axios configuration pattern
axios.defaults.baseURL = DEV ? '/api' : '';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
axios.defaults.withCredentials = true;

const axiosInstance = createAxiosInstance(logout);
```

### API Module Pattern

API calls are organized into domain-specific modules with consistent patterns:

```javascript
// API module pattern
export const postForecastData = payload => {
  return axiosObj({
    method: 'POST',
    url: '/svc/forecast/forecast',
    data: payload,
  });
};
```

### API Error Handling Pattern

A standardized approach to API error handling using custom error classes and toast notifications:

```javascript
// API error handling pattern
const handleApiResult = (result, dispatch, options) => {
  const { onSuccess, onFail, showToast } = options || {};
  
  if (isApiSuccess(result.status) || !result.status) {
    // Success handling
  } else {
    // Error handling with standardized messages
    const defaultAPIErrorMessage = DEFAULT_API_ERROR_MESSAGES[result.status];
    const errorMessage = getErrorMessage(result, defaultAPIErrorMessage);
    
    dispatch(showToastAction({ message: errorMessage, type: 'error' }));
    throw new HandledError(result);
  }
};
```

## Code Organization Patterns

### Feature-based Directory Structure

The codebase follows a feature-based organization:

```
src/
  ├── api/                  # API calls organized by domain
  ├── components/           # Reusable presentational components
  ├── containers/           # Container components organized by feature
  │   └── BusinessContexts/
  │       └── Forecast/     # Feature directory
  │           ├── components/  # Feature-specific components
  │           ├── index.jsx    # Main container component
  │           ├── reducer.js   # Feature slice
  │           └── styles.js    # Feature-specific styles
  ├── utils/                # Utility functions and helpers
  └── context/              # React context definitions
```

### Code Splitting Pattern

Dynamic imports and React.lazy are used for code splitting:

```javascript
// Code splitting pattern (example)
const ForecastPage = React.lazy(() => import('./containers/BusinessContexts/Forecast'));
```

## Feature Flag Patterns

### Feature Toggle Pattern

ConfigCat is used for feature toggles with a custom hook:

```javascript
// Feature flag pattern
export const useConfigCatFlag = (flag = '', addLoading = false, key = null, currentUserData = null) => {
  // Implementation...
  return addLoading ? [isLoading, enabledFlag] : enabledFlag;
};

// Usage
const isFeatureEnabled = useConfigCatFlag('feature_name');
```

## Styling Patterns

### Styled Components Pattern

The application uses styled-components for component-specific styling:

```javascript
// Styled components pattern
export const ForecastContainer = styled.div`
  padding: 20px;
  background-color: #fff;
`;

export const FormContainer = styled.div`
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 5px;
`;
```

## Error Handling Patterns

### Toast Notification Pattern

Error messages are displayed through toast notifications:

```javascript
// Toast notification pattern
dispatch(showToastAction({ message: errorMessage, type: 'error' }));
```

### Graceful UI Degradation Pattern

Components handle loading and error states gracefully:

```javascript
// UI degradation pattern
if (loading) {
  return <LoadingIndicator />;
}

if (error) {
  return <ErrorMessage>Error: {message}</ErrorMessage>;
}

return <ActualContent data={data} />;
```

## Routing Patterns

### Protected Routes Pattern

The application uses protected routes to prevent unauthorized access:

```javascript
// Protected route pattern
<PrivateRoute path="/forecast" component={ForecastPage} />
```

### Dynamic Route Injection

Routes can be dynamically registered, similar to reducers.

---

## Rules for LLM Development

When working on this codebase, follow these guidelines:

1. **State Management**:
   - Create new state using Redux Toolkit slices
   - Use createApiThunk for all API interactions
   - Create selectors using createDraftSafeSelector
   - Use the dynamic reducer injection pattern for new features

2. **Component Structure**:
   - Maintain separation between container and presentational components
   - Container components handle data and logic
   - Presentational components focus only on rendering
   - Extract reusable logic into custom hooks

3. **API Interactions**:
   - Add domain-specific API calls to the appropriate API module
   - Follow the established error handling patterns
   - Use the toast notification system for user feedback

4. **Styling**:
   - Use styled-components for component styling
   - Follow the established component structure

5. **Error Handling**:
   - Always include loading states
   - Always handle error states in UI
   - Use standardized error messages

6. **Type Safety**:
   - Use PropTypes for component props validation
   - Provide JSDoc comments for complex functions

By following these patterns, you'll ensure consistency with the existing codebase and make future maintenance easier.