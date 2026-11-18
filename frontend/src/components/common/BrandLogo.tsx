import React from 'react';
import pravasaLogo from '../../assets/pravasa-logo.png';
import pravasaIcon from '../../assets/pravasa-icon.png';

interface BrandLogoProps {
  /** 'full' displays the Pravasa logo with tagline; 'icon' displays the pin/plane mark only */
  variant?: 'full' | 'icon';
  /** 'dark' adds a crisp light container so dark-navy brand typography remains high-contrast */
  surface?: 'light' | 'dark';
  /** Tailwind classes applied to the inner <img> element */
  imgClassName?: string;
  /** Tailwind classes applied to the outer container */
  containerClassName?: string;
}

/**
 * Reusable Pravasa brand logo component ensuring consistent asset loading and contrast.
 */
export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = 'full',
  surface = 'light',
  imgClassName = 'h-10 w-auto object-contain',
  containerClassName = '',
}) => {
  const src = variant === 'icon' ? pravasaIcon : pravasaLogo;
  const alt = variant === 'icon' ? 'Pravasa' : 'Pravasa — Plan • Explore • Travel Smart';

  if (surface === 'dark') {
    const defaultPad = variant === 'icon' ? 'p-1 rounded-xl' : 'px-3 py-1 rounded-xl';
    return (
      <div
        className={`inline-flex items-center justify-center bg-white shadow-md shadow-black/20 ring-1 ring-white/25 ${defaultPad} ${containerClassName}`}
      >
        <img src={src} alt={alt} className={imgClassName} />
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center ${containerClassName}`}>
      <img src={src} alt={alt} className={imgClassName} />
    </div>
  );
};

