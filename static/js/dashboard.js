const config = {}
const context = {}
const lineChart = {}
const source = new EventSource("/chart-data");
$(document).ready(function () {
    openFirstTab();
    var canvasElements = document.getElementsByClassName("graph");
    setConfig(canvasElements);
    updateChart(canvasElements);
});

function updateChart(canvasElements) {
    source.onmessage = function (event) {
        const data = JSON.parse(event.data);
        for (var i = 0; i < canvasElements.length; i++) {
            var appareil = canvasElements[i].id;
            var time = data[appareil].time;
            var value = data[appareil].value;

            if (time != "" && value != "") {
                if (config[appareil].data.labels.length === 100) {
                    config[appareil].data.labels.shift();
                    config[appareil].data.datasets[0].data.shift();
                    config[appareil].data.datasets[0].borderColor.shift();
                    config[appareil].data.datasets[0].backgroundColor.shift();
                }

                config[appareil].data.labels.push(time);
                config[appareil].data.datasets[0].data.push(value);

                if (data[appareil].anomaly === 'false') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(54, 240, 92)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(54, 240, 92)');
                }
                else if (data[appareil].anomaly === 'true') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(255, 99, 132)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(255, 99, 132)');
                    //affiche une alerte
                    showAlert(appareil, value);
                    //ajouter une ligne dans historique
                    addHistorique(time, appareil, value);
                }
                else if (data[appareil].anomaly === 'null') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(0, 0, 0)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(0, 0, 0)');
                }

                lineChart[appareil].update();
            }
        }
    };
}

function setConfig(canvasElements) {
    for (var i = 0; i < canvasElements.length; i++) {
        appareil = canvasElements[i].id;
        config[appareil] = {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: "",
                    backgroundColor: [],
                    borderColor: [],
                    data: [],
                    fill: false,
                }],
            },
            options: {
                responsive: true,
                title: {
                    display: true,
                    text: `Relevé du capteur ${appareil}`,
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                },
                legend: {
                    display: false,
                },
                scales: {
                    xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Date & heure',
                        }
                    }],
                    yAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Valeur',
                        }
                    }]
                }
            }
        };

        context[appareil] = document.getElementById(appareil).getContext('2d');

        lineChart[appareil] = new Chart(context[appareil], config[appareil]);

    }
}

function check(appareil) {
    var thisCheckbox = document.getElementById(appareil.id);
    var container = document.getElementById(`container-${appareil.id.split("-")[1]}`)
    if (thisCheckbox.checked) {
        container.style.display = "block";
    } else {
        container.style.display = "none";
    }
}

function openFirstTab() {
    var tabcontent;
    var navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    navitem = document.getElementsByClassName("nav-item");

    tabcontent[0].style.display = "block";
    navitem[0].className += " active";
}


function openTab(evt, id) {
    var i, tabcontent, navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    navitem = document.getElementsByClassName("nav-item");
    for (i = 0; i < navitem.length; i++) {
        navitem[i].className = navitem[i].className.replace(" active", "");
    }
    document.getElementById("tab-" + id).style.display = "block";
    evt.currentTarget.className += " active";
}

function showAlert(appareil, value) {
    // Vérifions si le navigateur prend en charge les notifications
    if (!('Notification' in window)) {
        alert('Ce navigateur ne prend pas en charge la notification de bureau')
    }

    // Vérifions si les autorisations de notification ont déjà été accordées
    else if (Notification.permission === 'granted') {
        // Si tout va bien, créons une notification
        const notification = new Notification('Anomalie sur ' + appareil + ' -> valeur : ' + value)
    }

    // Sinon, nous devons demander la permission à l'utilisateur
    else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((permission) => {
            // Si l'utilisateur accepte, créons une notification
            if (permission === 'granted') {
                const notification = new Notification('Anomalie sur ' + appareil + ' -> valeur : ' + value)
            }
        })
    }

    // Enfin, si l'utilisateur a refusé les notifications, et que vous
    // voulez être respectueux, il n'est plus nécessaire de les déranger.

}

function addHistorique(time, appareil, value) {
    // Find a <table> element with id="myTable":
    var table = document.getElementById("table-historique");

    // Create an empty <tr> element and add it to the 1st position of the table:
    var row = table.insertRow(1);

    // Insert new cells (<td> elements) in the "new" <tr> element:
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);

    // Add some text to the new cells:
    cell1.innerHTML = time;
    cell2.innerHTML = appareil;
    cell3.innerHTML = value;
}