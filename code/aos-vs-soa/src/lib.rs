//! Array of structs vs struct of arrays, measured.
//!
//! Both layouts hold exactly the same weather station readings. The only thing that differs is how those
//! readings are arranged in memory. Every kernel here answers the same question: what is the total of the
//! `temperature` field?

/// One reading from a weather station.
///
/// Deliberately sized to exactly 32 bytes so that two readings fit in one 64 byte cache line. `temperature`
/// is stored in hundredths of a degree Celsius, which is how a lot of real sensor hardware reports it, and
/// which keeps the totals exact and reproducible.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Reading {
    pub timestamp: u64,
    pub station_id: u32,
    pub temperature: i32,
    pub humidity: f32,
    pub pressure: f32,
    pub wind_speed: f32,
    pub rainfall: f32,
}

/// The same readings, stored one array per field.
#[derive(Clone, Debug, Default)]
pub struct Readings {
    pub timestamp: Vec<u64>,
    pub station_id: Vec<u32>,
    pub temperature: Vec<i32>,
    pub humidity: Vec<f32>,
    pub pressure: Vec<f32>,
    pub wind_speed: Vec<f32>,
    pub rainfall: Vec<f32>,
}

impl Readings {
    pub fn len(&self) -> usize {
        self.temperature.len()
    }

    pub fn is_empty(&self) -> bool {
        self.temperature.is_empty()
    }
}

/// Total the temperature field, reading from an array of structs.
#[inline(never)]
pub fn total_temperature_aos(readings: &[Reading]) -> i64 {
    let mut total: i64 = 0;
    for reading in readings {
        total += reading.temperature as i64;
    }
    total
}

/// Total the temperature field, reading from a struct of arrays.
#[inline(never)]
pub fn total_temperature_soa(readings: &Readings) -> i64 {
    let mut total: i64 = 0;
    for &temperature in &readings.temperature {
        total += temperature as i64;
    }
    total
}

/// A tiny deterministic PRNG, so that every run generates identical data without pulling in a dependency.
struct XorShift64(u64);

impl XorShift64 {
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
}

/// Generate `n` readings as an array of structs.
pub fn generate_aos(n: usize) -> Vec<Reading> {
    let mut rng = XorShift64(0x5DEECE66D);
    (0..n)
        .map(|i| {
            let r = rng.next();
            Reading {
                timestamp: 1_700_000_000 + i as u64,
                station_id: (r % 512) as u32,
                // -2000 to 5000 hundredths of a degree, i.e. -20C to 50C.
                temperature: (r % 7001) as i32 - 2000,
                humidity: (r % 1001) as f32 / 10.0,
                pressure: 950.0 + (r % 1001) as f32 / 10.0,
                wind_speed: (r % 401) as f32 / 10.0,
                rainfall: (r % 201) as f32 / 10.0,
            }
        })
        .collect()
}

/// Generate the same `n` readings as a struct of arrays.
pub fn generate_soa(n: usize) -> Readings {
    let aos = generate_aos(n);
    let mut soa = Readings {
        timestamp: Vec::with_capacity(n),
        station_id: Vec::with_capacity(n),
        temperature: Vec::with_capacity(n),
        humidity: Vec::with_capacity(n),
        pressure: Vec::with_capacity(n),
        wind_speed: Vec::with_capacity(n),
        rainfall: Vec::with_capacity(n),
    };
    for reading in &aos {
        soa.timestamp.push(reading.timestamp);
        soa.station_id.push(reading.station_id);
        soa.temperature.push(reading.temperature);
        soa.humidity.push(reading.humidity);
        soa.pressure.push(reading.pressure);
        soa.wind_speed.push(reading.wind_speed);
        soa.rainfall.push(reading.rainfall);
    }
    soa
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reading_is_thirty_two_bytes() {
        assert_eq!(std::mem::size_of::<Reading>(), 32);
        assert_eq!(std::mem::align_of::<Reading>(), 8);
    }

    #[test]
    fn both_layouts_hold_the_same_data() {
        let aos = generate_aos(1000);
        let soa = generate_soa(1000);
        assert_eq!(aos.len(), soa.len());
        for (i, reading) in aos.iter().enumerate() {
            assert_eq!(reading.temperature, soa.temperature[i]);
            assert_eq!(reading.timestamp, soa.timestamp[i]);
        }
    }

    #[test]
    fn both_layouts_give_the_same_answer() {
        let aos = generate_aos(100_000);
        let soa = generate_soa(100_000);
        assert_eq!(total_temperature_aos(&aos), total_temperature_soa(&soa));
    }
}
