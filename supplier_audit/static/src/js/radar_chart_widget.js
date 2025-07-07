/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";

export class RadarChartWidget extends Component {
    setup() {
        this.chartRef = useRef("chart");
        this.chart = null;

        onMounted(() => {
            this.renderChart();
        });

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    renderChart() {
        if (!this.chartRef.el) return;

        const ctx = this.chartRef.el.getContext('2d');

        // Get chart data from the field
        let chartData;
        try {
            const dataStr = this.props.record.data[this.props.name];
            chartData = dataStr ? JSON.parse(dataStr) : this.getDefaultChartData();
        } catch (error) {
            console.error('Error parsing chart data:', error);
            chartData = this.getDefaultChartData();
        }

        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        // Add native JS callback functions (replacing invalid JSON strings)
        const optionsWithCallbacks = {
            ...chartData.options,
            scales: {
                ...(chartData.options?.scales || {}),
                r: {
                    ...(chartData.options?.scales?.r || {}),
                    ticks: {
                        ...chartData.options?.scales?.r?.ticks,
                        callback: function (value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                ...(chartData.options?.plugins || {}),
                tooltip: {
                    ...chartData.options?.plugins?.tooltip,
                    callbacks: {
                        ...chartData.options?.plugins?.tooltip?.callbacks,
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.r + '%';
                        }
                    }
                }
            }
        };

    // Create new chart
    this.chart = new Chart(ctx, {
        type: 'radar',
        data: chartData.data,
        options: optionsWithCallbacks
    });
}


    getDefaultChartData() {
        return {
            data: {
                labels: ['Management', 'Manufacturing', 'Production Readiness', 'Quality Assurance'],
                datasets: [{
                    label: 'Audit Results',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: '#36A2EB',
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    r: {
                        angleLines: { display: true },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: { stepSize: 25 }
                    }
                }
            }
        };
    }

    async willUpdateProps(nextProps) {
        if (this.props.record.data[this.props.name] !== nextProps.record.data[nextProps.name]) {
            await this.renderChart();
        }
    }
}

RadarChartWidget.template = "RadarChartWidget";
RadarChartWidget.supportedTypes = ["text"];

registry.category("fields").add("radar_chart", RadarChartWidget);