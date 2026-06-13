import { useState, useRef, useCallback } from 'react';

export default function BeforeAfterSlider({ beforeSrc, afterSrc }) {
  const [position, setPosition] = useState(50);
  const containerRef = useRef(null);
  const dragging = useRef(false);

  const updatePosition = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setPosition(pct);
  }, []);

  const onMouseDown = () => { dragging.current = true; };
  const onMouseUp = () => { dragging.current = false; };
  const onMouseMove = (e) => {
    if (dragging.current) updatePosition(e.clientX);
  };
  const onTouchMove = (e) => {
    updatePosition(e.touches[0].clientX);
  };

  if (!beforeSrc || !afterSrc) return null;

  return (
    <div
      ref={containerRef}
      className="before-after-container"
      onMouseDown={onMouseDown}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onMouseMove={onMouseMove}
      onTouchMove={onTouchMove}
      style={{ position: 'relative' }}
    >
      {/* After image (full width, behind) */}
      <img src={afterSrc} alt="After" style={{ width: '100%', display: 'block' }} />

      {/* Before image (clipped) */}
      <div className="before-image" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}>
        <img src={beforeSrc} alt="Before" />
      </div>

      {/* Slider line */}
      <div className="slider-line" style={{ left: `${position}%` }}>
        <div className="slider-handle">⇔</div>
      </div>

      {/* Labels */}
      <div style={{
        position: 'absolute', top: '8px', left: '12px',
        padding: '2px 8px', background: 'rgba(0,0,0,0.6)', borderRadius: '4px',
        fontSize: '11px', color: 'white', fontWeight: 600
      }}>Before</div>
      <div style={{
        position: 'absolute', top: '8px', right: '12px',
        padding: '2px 8px', background: 'rgba(0,0,0,0.6)', borderRadius: '4px',
        fontSize: '11px', color: 'white', fontWeight: 600
      }}>After</div>
    </div>
  );
}
