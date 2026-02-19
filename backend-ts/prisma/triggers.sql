CREATE OR REPLACE FUNCTION record_price_history()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        IF (NEW.current_price IS NOT NULL) THEN
            INSERT INTO price_history(product_id, price, timestamp)
            VALUES(NEW.id, NEW.current_price, NOW());
        END IF;
    ELSIF (TG_OP = 'UPDATE') THEN
        IF (OLD.current_price IS DISTINCT FROM NEW.current_price) THEN
            INSERT INTO price_history(product_id, price, timestamp)
            VALUES(NEW.id, NEW.current_price, NOW());
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_record_price_history ON products;
CREATE TRIGGER trigger_record_price_history
AFTER INSERT OR UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION record_price_history();
