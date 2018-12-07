var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/easy/cjfipwmk6eqii2rlhvjyymb2p',
    center: [11.0165, 48.1405],
    zoom: 18
});

map.on('load', function () {

    map.addLayer({
        "id": "pois",
        "type": "symbol",
        "source": {
            "type": "geojson",
            "data":{"type": "FeatureCollection","features": []}
        },
        "layout": {
            "icon-image": "{icon}-15",
            "text-field": "{title}",
            "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
            "text-offset": [0, 0.6],
            "text-size": 12,
            "text-anchor": "top"
        },
        "paint":{
            "text-color": "#000000",
        }
    });
    map.addLayer({
        "id": "uav",
        "type": "symbol",
        "source": {
            "type": "geojson",
            "data": {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [11.0165, 48.141]
                },
                "properties": {
                    "title": "UAV",
                    "icon": "drone"
                }
            }
        },
        "layout": {
            "icon-image": "{icon}-15",
            "icon-allow-overlap": true,
            "text-allow-overlap": true,
            "text-field": "{title}",
            "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
            "text-offset": [0, 0.6],
            "text-size": 10,
            "text-anchor": "top"
        },
        "paint":{
            "text-color": "#000000",
            
        }
    });
    map.addLayer({
        "id": "uavpath",
        "type": "line",
        "source": {
            "type": "geojson",
            "data": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": []
                }
            }
        },
        "layout": {
            "line-join": "round",
            "line-cap": "round"
        },
        "paint": {
            "line-color": "#ff0",
            "line-width": 2,
            "line-dasharray":[4,8]
        }
    });
    map.addControl(new mapboxgl.ScaleControl({
        maxWidth: 60,
        unit: 'metric'
    }));
});
