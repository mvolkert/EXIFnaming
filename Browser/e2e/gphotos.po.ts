import { Locator, Page } from "@playwright/test";
const fs = require('fs');

export class GPhotos {

    filenameText = '';

    name = '';


    constructor(private page: Page) {

    }

    infos(): Locator {
        return this.page.locator('[aria-label="Info öffnen"]')
    }

    filename(): Locator {
        return this.page.locator('[aria-label^="Dateiname"]')
    }

    options(): Locator {
        return this.page.locator('text=Upload unvollständig360°-VideoBewegung aktivierenTeilenBearbeitenZoomenInfoAls F >> [aria-label="Weitere Optionen"]')
    }

    addToAlbum(): Locator {
        return this.page.locator('text=Zu Album hinzufügen')
    }

    newAlbum(): Locator {
        return this.page.locator('li[role="option"]:has-text("Neues Album")')
    }

    listAlbum(name?: string): Locator {
        name = name ?? this.name;
        return this.page.locator(`[aria-label="Albumliste"] >> text="${name}"`)
    }

    editAlbum(): Locator {
        return this.page.locator('[aria-label="Albumnamen bearbeiten"]')
    }

    ok(): Locator {
        return this.page.locator('[aria-label="Fertig"]')
    }

    back(): Locator {
        return this.page.locator('[aria-label="Zurück"]')
    }

    album(name?: string): Locator {
        name = name ?? this.name;
        return this.page.locator(`li:has-text("${name}")`)
    }

    next(): Locator {
        return this.page.locator('[aria-label="Nächstes Foto ansehen"]')
    }

    async init() {
        this.filenameText = await this.filename().first().textContent() ?? '';
        this.name = this.filenameText?.split("_")[0] ?? '';
    }

    async openAddToAlbum(): Promise<void> {
        await this.options().click({ trial: true, delay: 10 });
        await this.options().click();
        await this.addToAlbum().click({ trial: true, delay: 200 });
        await this.addToAlbum().click();
        await this.newAlbum().waitFor({ state: 'visible', timeout: 5000 });
    }

    async searchPresentAlbum(name?: string): Promise<number> {
        name = name ?? this.name;
        let present = 0;
        for (let i = 0; i < 100; i++) {
            present = await this.listAlbum(name).count();
            if (present) {
                break;
            }
            await this.page.mouse.wheel(0, 100000);
            console.log(this.filenameText, name, present, i);
        }
        if (present >= 2) {
            console.log(this.filenameText, name, present, this.page.url(), await this.listAlbum(name).allInnerTexts())
        }
        console.log(this.filenameText, name, present, this.page.url());
        return present;
    }

    async createNewAlbum(name?: string): Promise<void> {
        name = name ?? this.name;
        await this.newAlbum().click();
        await this.editAlbum().click();
        await this.editAlbum().fill(name);
        await this.editAlbum().press('Enter');
        await this.ok().click();
        await this.back().click();
    }

    async updateFile(begin: string, end: string) {
        const content = `{"begin": "${begin}", "end": "${end}"}`
        require('fs').writeFileSync("configs/1.ts", content, 'utf8');
    }
}