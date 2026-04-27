import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { FluentProvider } from '@fluentui/react-components'
import '@fontsource-variable/sora'
import './index.css'
import App from './App'
import TagListPage from './pages/TagListPage'
import TagCreatePage from './pages/TagCreatePage'
import TagEditPage from './pages/TagEditPage'
import { aperamLightTheme } from './theme/aperamTheme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      retry: 1,
    },
  },
});

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/tags" replace /> },
      { path: 'tags', element: <TagListPage /> },
      { path: 'tags/new', element: <TagCreatePage /> },
      { path: 'tags/:id', element: <Navigate to="edit" replace /> },
      { path: 'tags/:id/edit', element: <TagEditPage /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <FluentProvider theme={aperamLightTheme}>
        <RouterProvider router={router} />
      </FluentProvider>
    </QueryClientProvider>
  </StrictMode>,
)
