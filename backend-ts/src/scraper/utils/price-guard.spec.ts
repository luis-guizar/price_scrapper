import {
  capUnreasonableOriginalPrice,
  BEAUTY_RULES,
  ELECTRONICS_RULES,
  OFFICE_RULES,
} from './price-guard';

describe('capUnreasonableOriginalPrice', () => {
  describe('ELECTRONICS_RULES', () => {
    it('returns originalPrice unchanged when within limit', () => {
      expect(
        capUnreasonableOriginalPrice('iPhone 16 Pro', 28000, 30000, ELECTRONICS_RULES),
      ).toBe(30000);
    });

    it('caps originalPrice to maxPrice when unreasonably high', () => {
      expect(
        capUnreasonableOriginalPrice('iPhone 16 Pro', 20000, 950000, ELECTRONICS_RULES),
      ).toBe(45000);
    });

    it('caps to currentPrice instead of maxPrice when currentPrice is higher', () => {
      // currentPrice > maxPrice means the product itself costs more than the cap — use currentPrice
      expect(
        capUnreasonableOriginalPrice('MacBook Air', 48000, 999999, ELECTRONICS_RULES),
      ).toBe(48000);
    });

    it('fires onCap callback with correct values', () => {
      const onCap = jest.fn();
      capUnreasonableOriginalPrice('Samsung TV 55"', 18000, 500000, ELECTRONICS_RULES, onCap);
      expect(onCap).toHaveBeenCalledWith('Samsung TV 55"', 500000, 45000);
    });

    it('does not fire onCap when price is within limit', () => {
      const onCap = jest.fn();
      capUnreasonableOriginalPrice('Nintendo Switch', 8000, 9000, ELECTRONICS_RULES, onCap);
      expect(onCap).not.toHaveBeenCalled();
    });

    it('matches case-insensitively', () => {
      expect(
        capUnreasonableOriginalPrice('MACBOOK AIR M3', 20000, 999999, ELECTRONICS_RULES),
      ).toBe(45000);
    });

    it('uses the first matching rule (most specific wins)', () => {
      // "macbook pro" should match the first rule (200000), not "laptop" (35000)
      const result = capUnreasonableOriginalPrice(
        'MacBook Pro 16 M4',
        90000,
        999999,
        ELECTRONICS_RULES,
      );
      expect(result).toBe(200000);
    });

    it('returns originalPrice unchanged for unrecognized product', () => {
      expect(
        capUnreasonableOriginalPrice('Juego de Mesa Monopoly', 500, 1200, ELECTRONICS_RULES),
      ).toBe(1200);
    });
  });

  describe('BEAUTY_RULES', () => {
    it('caps an inflated perfume price', () => {
      expect(
        capUnreasonableOriginalPrice('Perfume Chanel No.5 100ml', 3000, 85000, BEAUTY_RULES),
      ).toBe(8000);
    });

    it('returns price unchanged when within limit', () => {
      expect(
        capUnreasonableOriginalPrice('Lipstick MAC Ruby Woo', 600, 800, BEAUTY_RULES),
      ).toBe(800);
    });
  });

  describe('OFFICE_RULES', () => {
    it('caps an inflated printer price', () => {
      expect(
        capUnreasonableOriginalPrice('Impresora HP LaserJet Pro', 5000, 500000, OFFICE_RULES),
      ).toBe(20000);
    });

    it('returns price unchanged when within limit', () => {
      expect(
        capUnreasonableOriginalPrice('Silla de Oficina ergonomica', 6000, 7000, OFFICE_RULES),
      ).toBe(7000);
    });
  });
});
