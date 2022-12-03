import { test as testBase } from '@playwright/test';
import { GPhotos } from './gphotos.po';
import path from 'path';

const test = testBase.extend<{ gphotos: GPhotos }>({
    gphotos: async ({ page }, use) => {
        const gPage = new GPhotos(page);
        await use(gPage);
    }
})

test.use({
    storageState: 'login.json',
    baseURL: '',
    channel: 'msedge'
});



/*
const people = [];
for (const name of people) {
    test.skip(`test with ${name}`, async ({ page }) => {

        // Go to https://photos.google.com/u/0/
        await page.goto('https://photos.google.com/u/0/');

        // Click input[role="combobox"]
        await page.locator('input[role="combobox"]').click();

        // Fill input[role="combobox"]
        await page.locator('input[role="combobox"]').fill(name);

        // Click div[role="option"] div:has-text(name) >> nth=1
        await page.locator(`div[role="option"] div:has-text("${name}")`).nth(1).click();

        // Click text=Album ist leer.Fotos hinzufügen >> [aria-label="Fotos hinzufügen"]
        await page.locator('button:has-text("Fotos hinzufügen")').click();

        // Click text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen...Vom Computer auswählenFe >> input[role="combobox"]
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').click();

        // Fill text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen...Vom Computer auswählenFe >> input[role="combobox"]
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').fill(name);

        // Press Enter
        await page.locator('text=Zu Album hinzufügenIn meinen Fotos suchenWird geladen... >> input[role="combobox"]').press('Enter');

        // Click [aria-label="Alle Fotos mit diesem Zeitstempel auswählen\: date"]
        await page.locator(`[aria-label^="Alle Fotos mit diesem Zeitstempel auswählen"]`).first().click(); //\\: ${date}

        // Click button:has-text("Fertig")
        await page.locator('button:has-text("Fertig")').click();

    });
}
*/

const updateFile = (begin: string, end: string, i: number = 0) => {
    const content = `{"begin": "${begin}", "end": "${end}"}`;
    try {
        require('fs').writeFileSync(path.join(__dirname, `configs/${i}.json`), content, 'utf8');
    } catch (e) {
        console.log(e);
    }
}
const configs = new Array<{ begin: string, end: string }>();
for (let i = 0; i < 22; i++) {
    configs.push(JSON.parse(require('fs').readFileSync(path.join(__dirname, `configs/${i}.json`), 'utf8')))
}

test.describe.parallel('add to albums', () => {
    for (let i = 0; i < configs.length; i++) {
        let config = configs[i];
        test(`add to albums, start: ${config.begin}`, async ({ page, gphotos }) => {
            test.setTimeout(2147483647);
            await page.goto(config.begin);
            await gphotos.infos().click();
            while (page.url() != config.end) {
                await gphotos.init();

                await test.step(`${gphotos.filenameText}`, async () => {
                    const albums = await gphotos.album().count();
                    if (albums == 0) {
                        await gphotos.openAddToAlbum();
                        const present = await gphotos.searchPresentAlbum();
                        if (present) {
                            await gphotos.listAlbum().first().click();
                        } else {
                            await gphotos.createNewAlbum();
                        }
                    } else if (albums == 1) {
                        console.log('has album', gphotos.filenameText, gphotos.name, albums, page.url(), await gphotos.album().allInnerTexts())
                    } else if (albums > 1) {
                        console.log('has more albums', gphotos.filenameText, gphotos.name, albums, page.url(), await gphotos.album().allInnerTexts())
                    }
                    await gphotos.next().click();
                    await page.reload();
                    updateFile(page.url(), config.end, i)
                })
            }
        });
    }
});