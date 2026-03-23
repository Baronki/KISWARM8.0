import { useState } from 'react';
import { X, ChevronLeft, ChevronRight, ZoomIn } from 'lucide-react';

interface GalleryImage {
  id: string;
  src: string;
  title: string;
  description: string;
  category: string;
}

interface ImageGalleryProps {
  images: GalleryImage[];
  title?: string;
}

export default function ImageGallery({ images, title }: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<GalleryImage | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filter, setFilter] = useState('all');

  const categories = ['all', ...Array.from(new Set(images.map(img => img.category)))];
  const categoryList = categories as string[];
  const filteredImages = filter === 'all' ? images : images.filter(img => img.category === filter);

  const openLightbox = (image: GalleryImage, index: number) => {
    setSelectedImage(image);
    setSelectedIndex(index);
  };

  const closeLightbox = () => {
    setSelectedImage(null);
  };

  const goToPrevious = () => {
    const newIndex = (selectedIndex - 1 + filteredImages.length) % filteredImages.length;
    setSelectedImage(filteredImages[newIndex]);
    setSelectedIndex(newIndex);
  };

  const goToNext = () => {
    const newIndex = (selectedIndex + 1) % filteredImages.length;
    setSelectedImage(filteredImages[newIndex]);
    setSelectedIndex(newIndex);
  };

  return (
    <div className="w-full">
      {title && (
        <h2 className="text-3xl font-bold mb-8">{title}</h2>
      )}

      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2 mb-8">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setFilter(category)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === category
                ? 'bg-cyan-500 text-background'
                : 'bg-card border border-border hover:border-cyan-500/50'
            }`}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {/* Gallery Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {filteredImages.map((image, index) => (
          <div
            key={image.id}
            className="group relative overflow-hidden rounded-lg cursor-pointer"
            onClick={() => openLightbox(image, index)}
          >
            {/* Image Container */}
            <div className="relative h-64 bg-background overflow-hidden">
              <img
                src={image.src}
                alt={image.title}
                className="w-full h-full object-cover group-hover:scale-110 transition duration-500"
              />

              {/* Overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition duration-300 flex items-center justify-center">
                <div className="opacity-0 group-hover:opacity-100 transition duration-300 transform group-hover:scale-100 scale-75">
                  <ZoomIn className="w-12 h-12 text-white" />
                </div>
              </div>

              {/* Category Badge */}
              <div className="absolute top-3 right-3 bg-cyan-500/80 text-white text-xs font-bold px-3 py-1 rounded-full">
                {image.category}
              </div>
            </div>

            {/* Info */}
            <div className="bg-card border border-t-0 border-border p-4 group-hover:border-cyan-500/50 transition">
              <h3 className="font-bold text-sm mb-1 group-hover:text-cyan-400 transition">
                {image.title}
              </h3>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {image.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={closeLightbox}
        >
          <div
            className="relative max-w-4xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={closeLightbox}
              className="absolute -top-10 right-0 text-white hover:text-cyan-400 transition z-10"
            >
              <X className="w-8 h-8" />
            </button>

            {/* Image */}
            <div className="relative flex-1 overflow-hidden rounded-lg bg-background mb-4">
              <img
                src={selectedImage.src}
                alt={selectedImage.title}
                className="w-full h-full object-contain"
              />
            </div>

            {/* Info */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-xl font-bold mb-2 text-cyan-400">
                {selectedImage.title}
              </h3>
              <p className="text-muted-foreground mb-4">
                {selectedImage.description}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {selectedIndex + 1} / {filteredImages.length}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={goToPrevious}
                    className="p-2 bg-cyan-500/20 hover:bg-cyan-500/40 rounded-lg transition"
                  >
                    <ChevronLeft className="w-5 h-5 text-cyan-400" />
                  </button>
                  <button
                    onClick={goToNext}
                    className="p-2 bg-cyan-500/20 hover:bg-cyan-500/40 rounded-lg transition"
                  >
                    <ChevronRight className="w-5 h-5 text-cyan-400" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
