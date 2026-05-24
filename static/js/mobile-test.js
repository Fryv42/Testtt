/**
 * Mobile Viewport Tests
 * Проверяет корректность отображения на мобильных устройствах.
 * Запускать в консоли браузера или через Jest с jsdom.
 */

export class MobileViewportTester {
    constructor() {
        this.breakpoints = {
            mobileS: 320,
            mobileM: 375,
            mobileL: 425,
            tablet: 768,
            desktop: 1024
        };

        this.tests = [];
        this.results = [];
    }

    /**
     * Эмулирует viewport заданной ширины
     */
    setViewport(width) {
        if (typeof window !== 'undefined') {
            Object.defineProperty(window, 'innerWidth', {
                writable: true,
                configurable: true,
                value: width
            });
            window.dispatchEvent(new Event('resize'));
        }
    }

    /**
     * Проверяет минимальный размер touch-target
     * WCAG 2.5.5: Target Size (Minimum) — 44x44 px
     */
    testTouchTargets() {
        const interactiveElements = document.querySelectorAll(
            'button, .btn, .option-item, input[type="radio"], ' +
            'input[type="checkbox"], .nav-link, [role="button"], a'
        );

        const violations = [];

        interactiveElements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(el);
            const width = rect.width +
                parseInt(computedStyle.paddingLeft) +
                parseInt(computedStyle.paddingRight);
            const height = rect.height +
                parseInt(computedStyle.paddingTop) +
                parseInt(computedStyle.paddingBottom);

            if (width < 44 || height < 44) {
                violations.push({
                    element: el.tagName +
                        (el.className ? '.' + el.className.split(' ')[0] : ''),
                    width: Math.round(width),
                    height: Math.round(height),
                    text: el.textContent?.trim().substring(0, 30) || ''
                });
            }
        });

        return {
            test: 'Touch targets >= 44x44px',
            passed: violations.length === 0,
            violations,
            total: interactiveElements.length
        };
    }

    /**
     * Проверяет, что шрифт >= 14px на мобильных
     */
    testFontSizes() {
        const textElements = document.querySelectorAll(
            'p, .option-text, .question-text, input, button'
        );
        const violations = [];

        if (window.innerWidth <= 768) {
            textElements.forEach(el => {
                const fontSize = parseFloat(
                    window.getComputedStyle(el).fontSize
                );
                if (fontSize < 14 && fontSize > 0) {
                    violations.push({
                        element: el.tagName,
                        fontSize,
                        text: el.textContent?.trim().substring(0, 30) || ''
                    });
                }
            });
        }

        return {
            test: 'Font size >= 14px on mobile',
            viewport: window.innerWidth,
            passed: violations.length === 0,
            violations
        };
    }

    /**
     * Проверяет, что нет горизонтального скролла на мобильных
     */
    testNoHorizontalScroll() {
        const hasHorizontalScroll =
            document.documentElement.scrollWidth > window.innerWidth;

        return {
            test: 'No horizontal scroll on mobile',
            viewport: window.innerWidth,
            passed: !hasHorizontalScroll,
            scrollWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth
        };
    }

    /**
     * Проверяет, что кнопки на мобильных растянуты на всю ширину
     */
    testFullWidthButtons() {
        if (window.innerWidth > 768) {
            return {
                test: 'Full-width buttons (desktop — skipped)',
                passed: true
            };
        }

        const buttons = document.querySelectorAll('.btn-primary, .btn-submit');
        const violations = [];

        buttons.forEach(btn => {
            const btnWidth = btn.getBoundingClientRect().width;
            const containerWidth = btn
                .closest('.container, .card-body, .d-grid')
                ?.getBoundingClientRect().width;

            if (containerWidth && btnWidth < containerWidth * 0.8) {
                violations.push({
                    text: btn.textContent?.trim(),
                    btnWidth: Math.round(btnWidth),
                    containerWidth: Math.round(containerWidth)
                });
            }
        });

        return {
            test: 'Buttons full-width on mobile',
            passed: violations.length === 0,
            violations
        };
    }

    /**
     * Проверяет наличие meta viewport
     */
    testViewportMeta() {
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        const content = viewportMeta?.getAttribute('content') || '';

        const hasWidth = content.includes('width=device-width');
        const hasScale = content.includes('initial-scale=1');
        const hasUserScalable =
            content.includes('user-scalable=yes') ||
            content.includes('user-scalable=no');

        return {
            test: 'Meta viewport configured',
            passed: hasWidth && hasScale,
            content,
            details: { hasWidth, hasScale, hasUserScalable }
        };
    }

    /**
     * Проверяет атрибуты inputmode на мобильных формах
     */
    testInputModeAttributes() {
        const inputs = document.querySelectorAll('input');
        const violations = [];

        inputs.forEach(input => {
            const id = input.id;
            const type = input.type;
            const inputmode = input.getAttribute('inputmode');

            // Проверяем что для числовых полей есть inputmode
            if (
                (type === 'number' ||
                 type === 'tel' ||
                 id?.toLowerCase().includes('code')) &&
                !inputmode
            ) {
                violations.push({
                    id: id || '(no id)',
                    type,
                    suggestion:
                        type === 'number' ? 'numeric' :
                        type === 'tel' ? 'tel' : 'text'
                });
            }
        });

        return {
            test: 'Input mode attributes for mobile keyboards',
            passed: violations.length === 0,
            violations
        };
    }

    /**
     * Проверяет, что важные элементы не скрыты на мобильных
     */
    testNoHiddenCriticalElements() {
        const criticalSelectors = [
            '.quiz-timer',
            '.question-text',
            '.options-list',
            '.btn-submit',
            '#submitBtn',
            '.progress-bar-custom',
            '.navbar-brand'
        ];

        const hiddenElements = [];

        criticalSelectors.forEach(selector => {
            const el = document.querySelector(selector);
            if (el) {
                const style = window.getComputedStyle(el);
                if (
                    style.display === 'none' ||
                    style.visibility === 'hidden' ||
                    parseFloat(style.opacity) === 0
                ) {
                    hiddenElements.push(selector);
                }
            }
        });

        return {
            test: 'Critical elements visible on mobile',
            passed: hiddenElements.length === 0,
            hiddenElements
        };
    }

    /**
     * Запуск всех тестов
     */
    runAll() {
        // Сохраняем оригинальную ширину
        const originalWidth = window.innerWidth;

        const allResults = [];

        // Тестируем на всех брейкпоинтах
        Object.entries(this.breakpoints).forEach(([name, width]) => {
            this.setViewport(width);

            const results = {
                breakpoint: name,
                width,
                tests: [
                    this.testViewportMeta(),
                    this.testTouchTargets(),
                    this.testFontSizes(),
                    this.testNoHorizontalScroll(),
                    this.testFullWidthButtons(),
                    this.testInputModeAttributes(),
                    this.testNoHiddenCriticalElements()
                ]
            };

            results.summary = {
                total: results.tests.length,
                passed: results.tests.filter(t => t.passed).length,
                failed: results.tests.filter(t => !t.passed).length
            };

            allResults.push(results);
        });

        // Восстанавливаем оригинальную ширину
        this.setViewport(originalWidth);

        return allResults;
    }

    /**
     * Генерирует отчёт
     */
    generateReport() {
        const results = this.runAll();

        console.log('='.repeat(60));
        console.log('MOBILE VIEWPORT TEST REPORT');
        console.log('='.repeat(60));

        results.forEach(bp => {
            console.log(`\n--- ${bp.breakpoint} (${bp.width}px) ---`);
            console.log(`Passed: ${bp.summary.passed}/${bp.summary.total}`);

            bp.tests.forEach(test => {
                const icon = test.passed ? '✓' : '✗';
                console.log(`${icon} ${test.test}`);

                if (!test.passed && test.violations) {
                    test.violations.forEach(v => {
                        console.log(`  ↳ ${JSON.stringify(v)}`);
                    });
                }
            });
        });

        return results;
    }
}

// Экспорт для использования в тестах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MobileViewportTester };
}

// Автозапуск если в браузере и есть флаг
if (
    typeof window !== 'undefined' &&
    window.location.search.includes('mobile-test')
) {
    document.addEventListener('DOMContentLoaded', () => {
        const tester = new MobileViewportTester();
        window.mobileTestResults = tester.generateReport();
        console.log('Full results:', window.mobileTestResults);
    });
}