import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import {
  FluentProvider,
  createLightTheme,
  type BrandVariants,
} from '@fluentui/react-components'
import './index.css'
import App from './App'
import TagListPage from './pages/TagListPage'
import TagCreatePage from './pages/TagCreatePage'
import TagEditPage from './pages/TagEditPage'

// Aperam brand: purple #490B42, orange #F1511B
const aperamBrand: BrandVariants = {
  10: "#0D0209",
  20: "#1E0615",
  30: "#300A22",
  40: "#3C0B2E",
  50: "#490B42",
  60: "#5C1054",
  70: "#6F1666",
  80: "#7D1D73",
  90: "#8C2681",
  100: "#9A3290",
  110: "#A840A0",
  120: "#B550AF",
  130: "#C162BE",
  140: "#CC76CC",
  150: "#D88CDA",
  160: "#E4A4E7",
}

const aperamTheme = createLightTheme(aperamBrand)

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/tags" replace /> },
      { path: 'tags', element: <TagListPage /> },
      { path: 'tags/new', element: <TagCreatePage /> },
      { path: 'tags/:id', element: <div>Tag detail (coming soon)</div> },
      { path: 'tags/:id/edit', element: <TagEditPage /> },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <FluentProvider theme={aperamTheme}>
      <RouterProvider router={router} />
    </FluentProvider>
  </StrictMode>,
)
