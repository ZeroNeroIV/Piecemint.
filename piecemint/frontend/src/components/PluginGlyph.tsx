import { useState, type CSSProperties } from 'react';
import type { LucideIcon } from 'lucide-react';
import { piecemintPluginIconUrl } from '../lib/pluginIconUrl';

type PluginGlyphProps = {
  pluginId: string;
  hasIcon?: boolean;
  fallback: LucideIcon;
  size?: number;
  className?: string;
  imgClassName?: string;
  style?: CSSProperties;
};

export function PluginGlyph({
  pluginId,
  hasIcon,
  fallback: Fallback,
  size = 20,
  className = '',
  imgClassName = '',
  style,
}: PluginGlyphProps) {
  const [broken, setBroken] = useState(false);
  const showImg = Boolean(hasIcon && pluginId && !broken);

  if (showImg) {
    return (
      <img
        src={piecemintPluginIconUrl(pluginId)}
        alt=""
        width={size}
        height={size}
        className={`shrink-0 object-contain ${imgClassName} ${className}`}
        style={style}
        onError={() => setBroken(true)}
      />
    );
  }
  return (
    <Fallback
      size={size}
      strokeWidth={1.75}
      className={`shrink-0 ${className}`}
      style={style}
      aria-hidden
    />
  );
}
