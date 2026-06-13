import { Routes, Route } from 'react-router-dom';
import { useWebSocket } from './hooks/useWebSocket';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import FeaturePage from './pages/FeaturePage';
import BatchProcessing from './pages/BatchProcessing';
import ModelManager from './pages/ModelManager';
import Settings from './pages/Settings';

const FEATURES = [
  { path: 'background-removal', plugin: 'background_removal', title: 'Background Removal', icon: '✂️' },
  { path: 'face-enhancement', plugin: 'face_enhancement', title: 'Face Enhancement', icon: '✨' },
  { path: 'upscaling', plugin: 'upscaling', title: 'Image Upscaling', icon: '🔍' },
  { path: 'object-removal', plugin: 'object_removal', title: 'Object Removal', icon: '🧹' },
  { path: 'watermark-removal', plugin: 'watermark_removal', title: 'Watermark Removal', icon: '🔤' },
  { path: 'color-grading', plugin: 'color_grading', title: 'Color Grading', icon: '🎨' },
  { path: 'style-transfer', plugin: 'style_transfer', title: 'Style Transfer', icon: '🎭' },
  { path: 'cartoon-anime', plugin: 'cartoon_anime', title: 'Cartoon & Anime', icon: '🎌' },
  { path: 'headshot-generator', plugin: 'headshot_generator', title: 'AI Headshots', icon: '👔' },
  { path: 'wedding-studio', plugin: 'wedding_studio', title: 'Wedding Studio', icon: '💒' },
];

export default function App() {
  const ws = useWebSocket();

  return (
    <div className="app-layout">
      <Sidebar features={FEATURES} />
      <div className="main-content">
        <Header connected={ws.connected} />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard features={FEATURES} />} />
            {FEATURES.map(f => (
              <Route
                key={f.path}
                path={`/${f.path}`}
                element={<FeaturePage feature={f} ws={ws} />}
              />
            ))}
            <Route path="/batch" element={<BatchProcessing features={FEATURES} ws={ws} />} />
            <Route path="/models" element={<ModelManager />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
